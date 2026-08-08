"""Upgrade Crack the Core MRQs with provenance and less test-wise distractors.

The workflow is deliberately staged and reproducible:

    python tools/upgrade_crack_the_core_mrqs.py stage
    python tools/upgrade_crack_the_core_mrqs.py validate
    python tools/upgrade_crack_the_core_mrqs.py apply

``stage`` never changes the database. ``apply`` validates the staged artifacts,
creates a timestamped database backup, and applies pages and distractors in one
transaction.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import re
import shutil
import sqlite3
from collections import Counter
from pathlib import Path

import fitz

from upgrade_core_radiology_mrqs import has_giveaway, rewrite_distractor


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "edir_prep.db"
STAGE_DIR = ROOT / "data" / "crack_the_core_upgrade"
PAGE_STAGE = STAGE_DIR / "crack_the_core_page_map.json"
DISTRACTOR_STAGE = STAGE_DIR / "crack_the_core_distractor_upgrade.json"
AUDIT_STAGE = STAGE_DIR / "crack_the_core_upgrade_audit.json"
PAGE_DIR = ROOT / "data" / "crops" / "original_answer_pages"
SOURCE_DIR = Path(r"C:\Users\Razvan\Documents\Radiologie\EDiR")
BACKUP_DIR = Path(
    r"C:\Users\Razvan\Documents\Radiologie\backups\Crack_the_Core_upgrade"
)
SOURCE = "Crack the Core"
EXPECTED_QUESTIONS = 2545


# Complete rewrites for constructions where a lexical absolute-word swap would
# be ungrammatical, ambiguous, or still conspicuously test-wise. Each preserves
# the original false proposition and is checked against the same cited page.
MANUAL_DISTRACTOR_OVERRIDES = {
    (4328, 4): "Internal hernia is not a recognised complication after laparoscopic Roux-en-Y reconstruction",
    (4352, 1): "Small-bowel metastases are limited to direct peritoneal spread rather than haematogenous seeding",
    (4378, 3): "Target-like morphology is not described as a feature in the source",
    (4391, 2): "Misty mesentery is managed without interval imaging when lymphoma is excluded clinically",
    (4396, 4): "A caudate-to-right-lobe ratio greater than 0.75 is too nonspecific to aid diagnosis",
    (4446, 4): "The absence of stones excludes acalculous cholecystitis",
    (4483, 3): "These lesions are unsuitable for surgical treatment and have a poorer prognosis than pancreatic adenocarcinoma",
    (4510, 1): "Accessory spleen and splenosis are expected to lack tracer uptake",
    (4521, 2): "Echogenic perirenal fat is separate from, rather than continuous with, the renal sinus",
    (4560, 2): "A renal abscess is focal but characteristically ill-defined",
    (4675, 3): "The location of a vaginal metastasis is independent of the likely primary site",
    (4677, 3): "The dominant follicle usually remains below 5 mm by mid-cycle",
    (4751, 3): "Absence of an embryo six weeks after the last menstrual period meets diagnostic criteria for pregnancy failure",
    (4755, 3): "A yolk sac outside the uterus is suspicious but not diagnostic",
    (4776, 0): "Placenta accreta spectrum is described as occurring independently of recognised risk factors",
    (5010, 4): "A negative stress test excludes detectable left-main coronary disease",
    (5139, 2): "Longitudinal tears remain confined to the coronal plane without axial extension",
    (5195, 3): "Isolated discitis is common in adults and distinctly uncommon in children",
    (5206, 3): "Persistent viable tumour without chemotherapy-related tumour death",
    (5263, 0): "Further work-up is unnecessary because a popliteal cystic lesion is presumed to be a Baker cyst",
    (5273, 0): "It characteristically obliterates the joint space and causes diffuse osteoporosis",
    (5322, 3): "Arthrographic evaluation is abandoned when an alternative access route is unavailable",
    (5323, 2): "Needle placement should be avoided when confirmation is unobtainable",
    (5354, 3): "A temporal tap leaves the Doppler waveform unchanged",
    (5399, 1): "Lobar holoprosencephaly is incompatible with survival into adulthood",
    (5516, 0): "Metastases characteristically present as multiple rather than solitary lesions",
    (5520, 2): "Haemangiopericytoma is characterised by absent skull invasion and low vascularity",
    (5534, 4): "GBM is confined to the enhancing component on imaging",
    (5560, 4): "Toxoplasmosis presents as non-enhancing lesions without surrounding oedema",
    (5609, 0): "It is characteristically bilateral and independent of otomastoiditis",
    (5718, 0): "Severe atypical symptoms indicate uncomplicated post-dural puncture headache and are managed without imaging",
    (5740, 2): "Ependymoma is non-haemorrhagic and lacks a T2-dark cap",
    (5790, 2): "Fibrosing mediastinitis is excluded from the differential in the source",
    (5818, 2): "The bowel wall is characteristically paper-thin rather than thickened",
    (5907, 0): "The psoas is excluded from needle-related haematoma risk",
    (5926, 3): "New paraplegia after extensive aortic coverage can be observed without urgent intervention",
    (5953, 3): "Secondary patency means the graft has remained continuously patent",
    (5985, 1): "The right posterior duct does not drain into the left duct because the branching pattern is fixed",
    (5993, 2): "Rigors after forceful injection are a self-limiting reaction requiring observation alone",
    (5995, 4): "Segments 5 and 6 do not provide a usable transhepatic access route",
    (6013, 4): "Ablation at the visible tumour boundary is sufficient without a treatment margin",
    (6027, 3): "When upper-GI endoscopy is negative, prophylactic embolisation is directed to the inferior mesenteric artery",
    (6059, 4): "Antegrade conversion is not feasible after placement of a percutaneous nephrostomy",
    (6114, 2): "The lateral thoracic and intercostal perforators make a negligible contribution to breast blood supply",
    (6122, 1): "Lactation is a contraindication to breast biopsy",
    (6135, 0): "A milk fistula is regarded as a sterile complication",
    (6135, 2): "Active lactation is an absolute contraindication to breast biopsy",
    (6186, 3): "Inflammatory breast cancer is rarely metastatic at presentation",
    (6188, 0): "ADH is sufficiently indolent to be managed without surgical excision",
    (6201, 3): "A lesion without an ultrasound correlate does not require biopsy",
    (6232, 3): "Breast MRI eligibility is determined without a formal risk model",
    (6256, 4): "Local-recurrence surveillance relies on clinical assessment rather than imaging",
    (6258, 0): "Clinical follow-up is preferred to immediate imaging for nipple retraction or axillary adenopathy",
    (6259, 4): "Clinical assessment without imaging is appropriate for a palpable finding in a woman over 40",
    (6260, 4): "Women aged 30–39 with a palpable finding are managed initially without imaging",
    (6261, 0): "Young age is sufficient reason to omit follow-up",
    (6264, 2): "A palpable mass is sampled without image guidance",
    (6272, 3): "Adequate compression prevents clinically significant clip migration",
    (6275, 2): "Formal mammography training is not a stated requirement",
    (6278, 4): "A posterior-nipple-line difference establishes benignity and avoids callback",
    (6281, 2): "Prior mammograms are not used for comparison",
    (3772, 4): "Routine clinical review without interval chest radiography is recommended in elderly patients",
    (3983, 2): "It is described as confined to the heart rather than associated with systemic amyloid",
    (4002, 4): "Rastelli repair avoids later conduit replacement",
    (4026, 2): "A depressed fracture is defined without inward displacement",
    (4031, 3): "Clinical follow-up is sufficient because further imaging does not alter management",
    (4044, 2): "Symptomatic premature infants are first scanned at discharge rather than earlier",
    (4074, 0): "It lacks recognised cutaneous haemangioma associations",
    (4140, 4): "A preduodenal portal vein is independent of duodenal obstruction",
    (4219, 4): "Peutz–Jeghers syndrome lacks a recognised Sertoli-cell tumour association",
}

PDFS = {
    1: SOURCE_DIR / "Crack the CORE exam Volumul 1.pdf",
    2: SOURCE_DIR / "Crack the CORE exam Volumul 2.pdf",
}

# (DB chapter, case number) -> (volume, first zero-based PDF page,
# last zero-based PDF page). These are the exact source batches used during the
# original import. They prevent a similar fact elsewhere in the book from
# winning retrieval.
SESSION_PAGE_RANGES = {
    # Volume 1: GI
    (1, 14): (1, 260, 270), (1, 15): (1, 271, 282),
    (1, 16): (1, 283, 294), (1, 17): (1, 295, 306),
    (1, 18): (1, 307, 318), (1, 19): (1, 319, 330),
    (1, 20): (1, 331, 342), (1, 21): (1, 343, 348),
    # Volume 2: breast
    (2, 8): (2, 452, 463), (2, 9): (2, 464, 475),
    (2, 10): (2, 476, 487), (2, 11): (2, 488, 499),
    (2, 12): (2, 500, 511), (2, 13): (2, 512, 521),
    # Volume 1: cardiac
    (3, 7): (1, 114, 124), (3, 8): (1, 125, 136),
    (3, 9): (1, 137, 147),
    # Volume 1: thoracic
    (4, 10): (1, 44, 52), (4, 11): (1, 53, 64),
    (4, 12): (1, 65, 76), (4, 13): (1, 77, 88),
    (4, 14): (1, 89, 100), (4, 15): (1, 101, 111),
    # Volume 1: urinary, reproductive, adrenal
    (5, 9): (1, 352, 362), (5, 10): (1, 363, 374),
    (5, 11): (1, 375, 386), (5, 12): (1, 387, 397),
    (5, 13): (1, 400, 410), (5, 14): (1, 411, 422),
    (5, 15): (1, 423, 434), (5, 16): (1, 435, 446),
    (5, 17): (1, 447, 458), (5, 18): (1, 459, 467),
    (5, 19): (1, 470, 478),
    # Volume 1 thyroid/parathyroid, then Volume 2 head and neck
    (6, 12): (1, 479, 486), (6, 13): (2, 237, 248),
    (6, 14): (2, 249, 260), (6, 15): (2, 261, 272),
    (6, 16): (2, 273, 278),
    # Volume 2: vascular and interventional
    (7, 14): (2, 302, 312), (7, 15): (2, 313, 324),
    (7, 16): (2, 325, 334), (7, 17): (2, 335, 346),
    (7, 18): (2, 348, 357), (7, 19): (2, 358, 369),
    (7, 20): (2, 370, 381), (7, 21): (2, 382, 393),
    (7, 22): (2, 394, 405), (7, 23): (2, 406, 417),
    (7, 24): (2, 418, 429), (7, 25): (2, 430, 448),
    # Volume 2: musculoskeletal
    (8, 17): (2, 10, 21), (8, 18): (2, 22, 33),
    (8, 19): (2, 34, 45), (8, 20): (2, 46, 57),
    (8, 21): (2, 58, 69), (8, 22): (2, 70, 81),
    (8, 23): (2, 82, 93), (8, 24): (2, 94, 105),
    (8, 25): (2, 106, 117), (8, 26): (2, 118, 127),
    # Volume 2: neuroradiology (head/neck pages were routed above)
    (9, 15): (2, 130, 140), (9, 16): (2, 141, 152),
    (9, 17): (2, 153, 164), (9, 18): (2, 165, 176),
    (9, 19): (2, 177, 188), (9, 20): (2, 189, 200),
    (9, 21): (2, 201, 212), (9, 22): (2, 213, 224),
    (9, 23): (2, 225, 236), (9, 24): (2, 279, 284),
    (9, 25): (2, 285, 299),
    # Volume 1: paediatrics
    (10, 13): (1, 150, 160), (10, 14): (1, 161, 172),
    (10, 15): (1, 173, 184), (10, 16): (1, 185, 196),
    (10, 17): (1, 197, 208), (10, 18): (1, 209, 220),
    (10, 19): (1, 221, 232), (10, 20): (1, 233, 244),
    (10, 21): (1, 245, 258),
    # Volume 1: nuclear medicine
    (14, 6): (1, 493, 505), (14, 7): (1, 506, 520),
    (14, 8): (1, 521, 534), (14, 9): (1, 535, 549),
    (14, 10): (1, 550, 568),
}


def _tokens(value: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", value.casefold())


def _questions(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        """SELECT q.id, q.case_id, q.q_number, q.question_text, q.options,
                  q.source_locator, q.original_answer_pages,
                  a.correct_options, a.explanation,
                  c.case_number, ch.number AS chapter_number
           FROM questions q
           JOIN answers a ON a.question_id=q.id
           JOIN cases c ON c.id=q.case_id
           JOIN chapters ch ON ch.id=c.chapter_id
           WHERE c.library_key='edir' AND c.section='mrq' AND c.source=?
           ORDER BY ch.number, c.case_number, q.q_number""",
        (SOURCE,),
    ).fetchall()


def _page_texts() -> dict[tuple[int, int], dict]:
    needed = {
        (volume, page)
        for volume, first, last in SESSION_PAGE_RANGES.values()
        for page in range(first, last + 1)
    }
    result = {}
    for volume, path in PDFS.items():
        if not path.exists():
            raise FileNotFoundError(path)
        with fitz.open(path) as document:
            for _, index in sorted(key for key in needed if key[0] == volume):
                text = " ".join(document[index].get_text().split())
                result[(volume, index)] = {
                    "text": text,
                    "counts": Counter(_tokens(text)),
                }
    return result


def _rank(query: str, pages: list[tuple[int, int]], corpus: dict) -> list[tuple[float, tuple[int, int]]]:
    query_counts = Counter(_tokens(query))
    document_frequency = Counter()
    lengths = []
    for key in pages:
        counts = corpus[key]["counts"]
        document_frequency.update(counts.keys())
        lengths.append(sum(counts.values()))
    count = len(pages)
    average = sum(lengths) / max(1, count)
    ranked = []
    for key, length in zip(pages, lengths):
        counts = corpus[key]["counts"]
        score = 0.0
        for token, query_frequency in query_counts.items():
            frequency = counts.get(token, 0)
            if not frequency:
                continue
            inverse = math.log(
                (count - document_frequency[token] + 0.5)
                / (document_frequency[token] + 0.5)
                + 1
            )
            score += (
                inverse
                * frequency
                * 2.5
                / (frequency + 1.5 * (0.25 + 0.75 * length / average))
                * min(query_frequency, 3)
            )
        ranked.append((score, key))
    return sorted(ranked, reverse=True)


def _book_page(volume: int, pdf_index: int) -> int:
    # Volume 1: printed = 1-based PDF + 1. Volume 2: printed = 0-based PDF.
    return pdf_index + 2 if volume == 1 else pdf_index


def _render_page(volume: int, index: int) -> str:
    filename = f"crack-the-core-v{volume}-source_p{index + 1:03d}.jpg"
    destination = PAGE_DIR / filename
    if not destination.exists():
        PAGE_DIR.mkdir(parents=True, exist_ok=True)
        with fitz.open(PDFS[volume]) as document:
            pixmap = document[index].get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
            destination.write_bytes(pixmap.tobytes("jpeg", jpg_quality=78))
    return destination.relative_to(ROOT).as_posix()


def _json_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _rewrite_crack_distractor(question_id: int, index: int, text: str) -> str:
    override = MANUAL_DISTRACTOR_OVERRIDES.get((question_id, index))
    if override:
        return override
    revised = rewrite_distractor(text)
    # A terminal "only" is a test-wise qualifier; removing it leaves the
    # specific competing diagnosis, modality, location, or threshold intact.
    revised = re.sub(r"\s+in typical cases(?=[.!?]?$)", "", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bprimarily weakly\b", "weakly", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bnearly most patients\b", "most patients", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bMost patients ([a-z]+)s\b", r"Most patients \1", revised)
    revised = re.sub(r"\bmore than 90% of cases\b", "most cases", revised, flags=re.IGNORECASE)
    replacements = {
        "routine pure calcification finding": "a pure calcification finding",
        "routine palpable finding": "a palpable finding",
        "routine simple cyst": "a simple cyst",
        "routine tight vessel": "a tight vessel",
        "routine catheter injection": "catheter injection",
        "routine flap recurrence": "flap recurrence",
        "routine fracture": "fractures",
        "routine finding": "a finding",
        "routine mammogram": "screening mammograms",
    }
    for source, replacement in replacements.items():
        revised = re.sub(rf"\b{re.escape(source)}\b", replacement, revised, flags=re.IGNORECASE)
    revised = re.sub(r"\s+", " ", revised).strip()
    return revised


def stage() -> None:
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    rows = _questions(connection)
    connection.close()
    if len(rows) != EXPECTED_QUESTIONS:
        raise ValueError(f"Expected {EXPECTED_QUESTIONS} questions, found {len(rows)}")
    session_keys = {(row["chapter_number"], row["case_number"]) for row in rows}
    if session_keys != set(SESSION_PAGE_RANGES):
        raise ValueError("Database sessions differ from the audited source-batch map")

    corpus = _page_texts()
    page_updates = []
    for row in rows:
        session = (row["chapter_number"], row["case_number"])
        volume, first, last = SESSION_PAGE_RANGES[session]
        candidates = [(volume, index) for index in range(first, last + 1)]
        options = json.loads(row["options"])
        correct = json.loads(row["correct_options"])
        query = " ".join(
            [row["question_text"], *(options[index] for index in correct), row["explanation"] or ""]
        )
        ranked = _rank(query, candidates, corpus)
        score, (_, page_index) = ranked[0]
        runner_up = ranked[1][0] if len(ranked) > 1 else 0.0
        page_updates.append(
            {
                "question_id": row["id"],
                "case_id": row["case_id"],
                "chapter_number": row["chapter_number"],
                "case_number": row["case_number"],
                "q_number": row["q_number"],
                "source_locator_before": json.loads(row["source_locator"] or "{}"),
                "original_answer_pages_before": json.loads(row["original_answer_pages"] or "[]"),
                "source_locator": {
                    "file": PDFS[volume].name,
                    "pdf_pages": [page_index + 1],
                    "book_pages": [_book_page(volume, page_index)],
                },
                "original_answer_pages": [_render_page(volume, page_index)],
                "retrieval_score": round(score, 4),
                "runner_up_score": round(runner_up, 4),
                "score_margin": round(score - runner_up, 4),
                "session_pdf_range": [first + 1, last + 1],
            }
        )

    page_payload = {
        "schema_version": 1,
        "source": SOURCE,
        "question_count": len(page_updates),
        "session_count": len(session_keys),
        "updates": page_updates,
    }
    locator_by_id = {item["question_id"]: item["source_locator"] for item in page_updates}
    distractor_updates = []
    changed_options = 0
    for row in rows:
        before = json.loads(row["options"])
        correct = set(json.loads(row["correct_options"]))
        after = list(before)
        changed = []
        for index, option in enumerate(before):
            if index in correct or not has_giveaway(option):
                continue
            after[index] = _rewrite_crack_distractor(row["id"], index, option)
            changed.append(index)
        if not changed:
            continue
        if len(after) != 5 or len(set(after)) != 5:
            raise ValueError(f"Question {row['id']} has invalid revised options")
        if any(has_giveaway(after[index]) for index in changed):
            raise ValueError(f"Question {row['id']} retains giveaway wording")
        changed_options += len(changed)
        distractor_updates.append(
            {
                "question_id": row["id"],
                "chapter_number": row["chapter_number"],
                "case_number": row["case_number"],
                "q_number": row["q_number"],
                "question_text": row["question_text"],
                "correct_options": sorted(correct),
                "source_locator": locator_by_id[row["id"]],
                "options_before": before,
                "options_after": after,
                "changed_indices": changed,
                "explanation": row["explanation"],
            }
        )

    distractor_payload = {
        "schema_version": 1,
        "source": SOURCE,
        "question_count": len(rows),
        "questions_changed": len(distractor_updates),
        "distractors_changed": changed_options,
        "updates": distractor_updates,
    }
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    PAGE_STAGE.write_text(json.dumps(page_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    DISTRACTOR_STAGE.write_text(json.dumps(distractor_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "questions": len(rows), "sessions": len(session_keys),
        "unique_source_pages": len({u["original_answer_pages"][0] for u in page_updates}),
        "questions_with_revised_distractors": len(distractor_updates),
        "distractors_revised": changed_options,
        "minimum_retrieval_margin": min(u["score_margin"] for u in page_updates),
    }, indent=2))


def validate(*, require_database_match: bool = True) -> dict:
    pages = json.loads(PAGE_STAGE.read_text(encoding="utf-8"))
    distractors = json.loads(DISTRACTOR_STAGE.read_text(encoding="utf-8"))
    errors = []
    if pages.get("question_count") != EXPECTED_QUESTIONS or len(pages.get("updates", [])) != EXPECTED_QUESTIONS:
        errors.append("page artifact does not contain exactly 2,545 questions")
    if pages.get("session_count") != 86:
        errors.append("page artifact does not contain exactly 86 sessions")
    page_ids = [item.get("question_id") for item in pages.get("updates", [])]
    if len(set(page_ids)) != len(page_ids):
        errors.append("page artifact contains duplicate question IDs")
    for item in pages.get("updates", []):
        locator = item.get("source_locator") or {}
        original = item.get("original_answer_pages") or []
        key = (item.get("chapter_number"), item.get("case_number"))
        volume, first, last = SESSION_PAGE_RANGES.get(key, (None, None, None))
        pdf_page = (locator.get("pdf_pages") or [None])[0]
        expected_file = PDFS.get(volume, Path()).name
        if locator.get("file") != expected_file or pdf_page is None or not first + 1 <= pdf_page <= last + 1:
            errors.append(f"question {item.get('question_id')}: invalid source locator")
        if len(original) != 1 or not (ROOT / original[0]).is_file():
            errors.append(f"question {item.get('question_id')}: source-page asset missing")

    updates = distractors.get("updates") or []
    if distractors.get("question_count") != EXPECTED_QUESTIONS:
        errors.append("distractor artifact question count is invalid")
    changed_total = 0
    for item in updates:
        before = item.get("options_before") or []
        after = item.get("options_after") or []
        correct = set(item.get("correct_options") or [])
        changed = item.get("changed_indices") or []
        if len(before) != 5 or len(after) != 5 or len(set(after)) != 5:
            errors.append(f"question {item.get('question_id')}: invalid options")
            continue
        if any(index in correct or not 0 <= index < 5 for index in changed):
            errors.append(f"question {item.get('question_id')}: correct option changed")
        if any(before[index] == after[index] for index in changed):
            errors.append(f"question {item.get('question_id')}: staged option unchanged")
        if any(before[index] != after[index] for index in range(5) if index not in changed):
            errors.append(f"question {item.get('question_id')}: unstaged option changed")
        if any(has_giveaway(after[index]) for index in changed):
            errors.append(f"question {item.get('question_id')}: giveaway remains")
        if not item.get("source_locator"):
            errors.append(f"question {item.get('question_id')}: provenance missing")
        changed_total += len(changed)
    if distractors.get("distractors_changed") != changed_total:
        errors.append("distractor count differs from staged indices")

    if require_database_match:
        connection = sqlite3.connect(DB)
        connection.row_factory = sqlite3.Row
        rows = _questions(connection)
        by_id = {row["id"]: row for row in rows}
        connection.close()
        if len(rows) != EXPECTED_QUESTIONS:
            errors.append("database question count changed")
        for item in pages.get("updates", []):
            row = by_id.get(item["question_id"])
            if row is None:
                errors.append(f"question {item['question_id']}: absent from database")
                continue
            if json.loads(row["source_locator"] or "{}") != item["source_locator_before"]:
                errors.append(f"question {item['question_id']}: source locator changed since staging")
            if json.loads(row["original_answer_pages"] or "[]") != item["original_answer_pages_before"]:
                errors.append(f"question {item['question_id']}: source pages changed since staging")
        for item in updates:
            row = by_id.get(item["question_id"])
            if row is None or json.loads(row["options"]) != item["options_before"]:
                errors.append(f"question {item['question_id']}: options changed since staging")

    if errors:
        raise ValueError("Validation failed:\n- " + "\n- ".join(errors[:40]))
    report = {
        "questions": EXPECTED_QUESTIONS,
        "sessions": 86,
        "page_mappings": len(page_ids),
        "unique_source_pages": len({u["original_answer_pages"][0] for u in pages["updates"]}),
        "questions_with_revised_distractors": len(updates),
        "distractors_revised": changed_total,
        "remaining_giveaway_flags": 0,
        "stage_hashes": {
            PAGE_STAGE.name: _json_hash(pages),
            DISTRACTOR_STAGE.name: _json_hash(distractors),
        },
    }
    print(json.dumps(report, indent=2))
    return report


def apply() -> None:
    report = validate(require_database_match=True)
    pages = json.loads(PAGE_STAGE.read_text(encoding="utf-8"))
    distractors = json.loads(DISTRACTOR_STAGE.read_text(encoding="utf-8"))
    options_by_id = {item["question_id"]: item["options_after"] for item in distractors["updates"]}
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"edir_prep.before_crack_the_core_upgrade_{stamp}.db"
    shutil.copy2(DB, backup)
    connection = sqlite3.connect(DB)
    try:
        connection.execute("BEGIN IMMEDIATE")
        for item in pages["updates"]:
            fields = [
                json.dumps(item["source_locator"], ensure_ascii=False),
                json.dumps(item["original_answer_pages"], ensure_ascii=False),
            ]
            if item["question_id"] in options_by_id:
                connection.execute(
                    "UPDATE questions SET source_locator=?, original_answer_pages=?, options=? WHERE id=?",
                    (*fields, json.dumps(options_by_id[item["question_id"]], ensure_ascii=False), item["question_id"]),
                )
            else:
                connection.execute(
                    "UPDATE questions SET source_locator=?, original_answer_pages=? WHERE id=?",
                    (*fields, item["question_id"]),
                )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    report.update({
        "applied_at": dt.datetime.now().astimezone().isoformat(),
        "database_backup": str(backup),
        "transaction": "committed",
    })
    AUDIT_STAGE.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("stage", "validate", "apply"))
    args = parser.parse_args()
    if args.command == "stage":
        stage()
    elif args.command == "validate":
        validate()
    else:
        apply()


if __name__ == "__main__":
    main()
