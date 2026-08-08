"""Validate, audit, and import one approved UEFA CFM MRQ session.

Validation is the default CLI action. Database insertion requires the explicit
``--import-approved`` flag so the per-PDF approval gate cannot be bypassed by
accident.
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import re
import shutil
from collections import Counter
from pathlib import Path

try:
    import fitz
except ImportError:  # pragma: no cover - reported by validation when required
    fitz = None

from core.database import (
    CFM_CHAPTER_NUMBER,
    CFM_CHAPTER_TITLE,
    DB_PATH,
    LIBRARY_UEFA_CFM,
    get_conn,
    init_db,
)
from core.insert_cases import (
    ANSWER_PAGES_DIR,
    CROPS_DIR,
    _resolve_page_crops,
    _slug,
)


CFM_SCHEMA_VERSION = 1
MIN_QUESTIONS = 80
MAX_QUESTIONS = 120
ORAL_EXAM_CATEGORIES = {
    "application": (0.40, 0.50),
    "explanation": (0.30, 0.40),
    "factual_anchor": (0.15, 0.25),
}
DISTRACTOR_GIVEAWAY_RE = re.compile(
    r"\b(?:all|always|never|only|every|entire|entirely|automatic(?:ally)?|"
    r"guarantee(?:d|s)?|permanent(?:ly)?|impossible|identical|exclusively|"
    r"regardless|abolish(?:ed|ing|ment)?|eliminat(?:e|es|ed|ing|ion)|"
    r"prohibit(?:s|ed|ing|ion)?|immunity|exemption)\b|"
    r"astrolog|personality types|random action",
    re.IGNORECASE,
)


def load_payload(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.casefold()).strip()


def _validate_locator(locator, source_pdf: str, page_count: int | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(locator, dict):
        return ["source_locator must be an object"]
    if locator.get("file") != source_pdf:
        errors.append("source_locator.file must equal source_pdf")
    for key in ("pdf_pages", "handbook_pages"):
        pages = locator.get(key)
        if not isinstance(pages, list) or not pages:
            errors.append(f"source_locator.{key} must be a non-empty list")
            continue
        if any(isinstance(page, bool) or not isinstance(page, int) or page < 1 for page in pages):
            errors.append(f"source_locator.{key} must contain positive integers")
    if page_count is not None:
        for page in locator.get("pdf_pages") or []:
            if isinstance(page, int) and page > page_count:
                errors.append(
                    f"source_locator PDF page {page} exceeds {page_count} pages"
                )
    return errors


def _validate_crop(crop, page_count: int | None) -> list[str]:
    errors: list[str] = []
    if not isinstance(crop, dict):
        return ["page_crops entries must be objects"]
    page = crop.get("pdf_page")
    if isinstance(page, bool) or not isinstance(page, int) or page < 1:
        errors.append("page_crops.pdf_page must be a positive integer")
    elif page_count is not None and page > page_count:
        errors.append(f"page crop PDF page {page} exceeds {page_count} pages")
    bbox = crop.get("bbox")
    if not isinstance(bbox, dict):
        errors.append("page_crops.bbox must be an object")
    else:
        try:
            left, top, right, bottom = (
                float(bbox[name]) for name in ("left", "top", "right", "bottom")
            )
            if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
                errors.append("page crop bbox must be normalized within 0..1")
        except (KeyError, TypeError, ValueError):
            errors.append("page crop bbox needs numeric left/top/right/bottom")
    if not str(crop.get("caption") or "").strip():
        errors.append("page crops require a caption")
    return errors


def validate_session(payload: dict, pdf_path: str | Path | None = None) -> list[str]:
    errors: list[str] = []
    if payload.get("schema_version") != CFM_SCHEMA_VERSION:
        errors.append(f"schema_version must be {CFM_SCHEMA_VERSION}")
    if payload.get("library_key") != LIBRARY_UEFA_CFM:
        errors.append(f"library_key must be {LIBRARY_UEFA_CFM}")
    if payload.get("chapter_number") != CFM_CHAPTER_NUMBER:
        errors.append(f"chapter_number must be {CFM_CHAPTER_NUMBER}")
    if not str(payload.get("session_title") or "").strip():
        errors.append("session_title is required")
    source_pdf = str(payload.get("source_pdf") or "").strip()
    if not source_pdf.lower().endswith(".pdf"):
        errors.append("source_pdf must be a PDF filename")

    page_count = None
    if pdf_path is not None:
        pdf_path = Path(pdf_path)
        if not pdf_path.is_file():
            errors.append(f"PDF not found: {pdf_path}")
        elif pdf_path.name != source_pdf:
            errors.append("The supplied PDF filename does not match source_pdf")
        elif fitz is None:
            errors.append("PyMuPDF is required for page validation")
        else:
            with fitz.open(pdf_path) as doc:
                page_count = len(doc)

    questions = payload.get("questions")
    if not isinstance(questions, list):
        return errors + ["questions must be a list"]
    if not MIN_QUESTIONS <= len(questions) <= MAX_QUESTIONS:
        errors.append(
            f"one CFM session must contain {MIN_QUESTIONS}-{MAX_QUESTIONS} questions"
        )

    expected_numbers = list(range(1, len(questions) + 1))
    actual_numbers = [question.get("q_number") for question in questions]
    if actual_numbers != expected_numbers:
        errors.append("q_number values must be unique and consecutive from 1")

    correct_count_distribution: Counter[int] = Counter()
    correct_position_distribution: Counter[int] = Counter()
    oral_exam_distribution: Counter[str] = Counter()
    normalised_stems: list[tuple[int, str]] = []
    option_sets: dict[tuple[str, ...], int] = {}
    for index, question in enumerate(questions, 1):
        prefix = f"Q{index}"
        oral_exam_category = question.get("oral_exam_category")
        if oral_exam_category not in ORAL_EXAM_CATEGORIES:
            errors.append(
                f"{prefix}: oral_exam_category must be application, explanation, "
                "or factual_anchor"
            )
        else:
            oral_exam_distribution[oral_exam_category] += 1
        stem = str(question.get("question_text") or "").strip()
        if len(stem) < 20:
            errors.append(f"{prefix}: question_text is too short")
        if re.search(
            r"\b(?:not(?!-)|incorrect|false|except)\b", stem, re.IGNORECASE
        ):
            errors.append(f"{prefix}: negative stems are not allowed")
        if stem:
            normalised_stems.append((index, _normalise(stem)))
        if question.get("q_type") != "multiple_choice":
            errors.append(f"{prefix}: q_type must be multiple_choice")
        options = question.get("options")
        if not isinstance(options, list) or len(options) != 5:
            errors.append(f"{prefix}: exactly five options are required")
            options = []
        elif len({_normalise(str(option)) for option in options}) != 5:
            errors.append(f"{prefix}: options must be distinct")
        else:
            option_key = tuple(sorted(_normalise(str(option)) for option in options))
            if option_key in option_sets:
                errors.append(
                    f"{prefix}: repeats the option set from Q{option_sets[option_key]}"
                )
            else:
                option_sets[option_key] = index
        answer = question.get("answer")
        if not isinstance(answer, dict):
            errors.append(f"{prefix}: answer must be an object")
            answer = {}
        correct = answer.get("correct_options")
        if (
            not isinstance(correct, list)
            or not 1 <= len(correct) <= 4
            or any(isinstance(value, bool) or not isinstance(value, int) for value in correct)
            or len(set(correct)) != len(correct)
            or any(value < 0 or value >= 5 for value in correct)
        ):
            errors.append(f"{prefix}: correct_options must contain 1-4 unique indices 0..4")
        else:
            correct_count_distribution[len(correct)] += 1
            correct_position_distribution.update(correct)
            if options:
                correct_word_mean = sum(
                    len(str(options[index]).split()) for index in correct
                ) / len(correct)
                for option_index, option in enumerate(options):
                    if option_index in correct:
                        continue
                    if DISTRACTOR_GIVEAWAY_RE.search(str(option)):
                        errors.append(
                            f"{prefix}: distractor {option_index + 1} contains "
                            "giveaway absolute or implausible wording"
                        )
                    word_ratio = len(str(option).split()) / max(correct_word_mean, 1)
                    if word_ratio > 3.0 or word_ratio < 0.33:
                        errors.append(
                            f"{prefix}: distractor {option_index + 1} has a "
                            "conspicuous length difference from the correct options"
                        )
        explanation = str(answer.get("explanation") or "").strip()
        if len(explanation) < 80:
            errors.append(f"{prefix}: model oral answer is too short")
        errors.extend(
            f"{prefix}: {message}"
            for message in _validate_locator(
                question.get("source_locator"), source_pdf, page_count
            )
        )
        for crop in question.get("page_crops") or []:
            errors.extend(
                f"{prefix}: {message}"
                for message in _validate_crop(crop, page_count)
            )

    if len(questions) >= 10:
        for category, (minimum, maximum) in ORAL_EXAM_CATEGORIES.items():
            rate = oral_exam_distribution[category] / len(questions)
            if not minimum <= rate <= maximum:
                errors.append(
                    f"oral-exam category {category} occurs in {rate:.0%}; "
                    f"expected {minimum:.0%}-{maximum:.0%}"
                )
        missing_counts = sorted(set(range(1, 5)) - set(correct_count_distribution))
        if missing_counts:
            errors.append(
                "answer-count distribution must include 1, 2, 3, and 4 correct options"
            )
        if correct_count_distribution and max(correct_count_distribution.values()) > len(questions) * 0.55:
            errors.append("one correct-answer count dominates more than 55% of the bank")
        for position in range(5):
            rate = correct_position_distribution[position] / max(len(questions), 1)
            if not 0.30 <= rate <= 0.70:
                errors.append(
                    f"correct-option position {position + 1} occurs in {rate:.0%}; expected 30-70%"
                )

    for left_index in range(len(normalised_stems)):
        q_left, left = normalised_stems[left_index]
        for q_right, right in normalised_stems[left_index + 1 :]:
            if left == right or difflib.SequenceMatcher(None, left, right).ratio() >= 0.88:
                errors.append(f"Q{q_left} and Q{q_right} are near-duplicate stems")

    return errors


def audit_session(payload: dict) -> dict:
    questions = payload.get("questions") or []
    correct_counts: Counter[int] = Counter()
    positions: Counter[int] = Counter()
    crops = 0
    pdf_pages: set[int] = set()
    oral_exam_categories: Counter[str] = Counter()
    distractor_count = 0
    distractor_giveaway_flags = 0
    distractor_length_flags = 0
    for question in questions:
        correct = (question.get("answer") or {}).get("correct_options") or []
        correct_counts[len(correct)] += 1
        positions.update(correct)
        crops += len(question.get("page_crops") or [])
        pdf_pages.update((question.get("source_locator") or {}).get("pdf_pages") or [])
        oral_exam_categories[question.get("oral_exam_category")] += 1
        options = question.get("options") or []
        if correct and options:
            correct_word_mean = sum(
                len(str(options[index]).split()) for index in correct
            ) / len(correct)
            for option_index, option in enumerate(options):
                if option_index in correct:
                    continue
                distractor_count += 1
                distractor_giveaway_flags += bool(
                    DISTRACTOR_GIVEAWAY_RE.search(str(option))
                )
                word_ratio = len(str(option).split()) / max(correct_word_mean, 1)
                distractor_length_flags += word_ratio > 3.0 or word_ratio < 0.33
    count = len(questions)
    return {
        "session_title": payload.get("session_title"),
        "source_pdf": payload.get("source_pdf"),
        "question_count": count,
        "oral_exam_blueprint": {
            category: {
                "count": oral_exam_categories[category],
                "rate": round(oral_exam_categories[category] / max(count, 1), 3),
            }
            for category in ORAL_EXAM_CATEGORIES
        },
        "distractor_audit": {
            "count": distractor_count,
            "giveaway_flags": distractor_giveaway_flags,
            "conspicuous_length_flags": distractor_length_flags,
        },
        "correct_answer_counts": {
            str(key): correct_counts[key] for key in range(1, 5)
        },
        "correct_position_rates": {
            chr(97 + position): round(positions[position] / max(count, 1), 3)
            for position in range(5)
        },
        "cited_pdf_pages": sorted(pdf_pages),
        "diagram_crops": crops,
    }


def _render_original_source_pages(
    pdf_pages: list[int], doc, source_slug: str
) -> list[str]:
    """Render complete cited PDF spreads for question-level answer expanders."""
    ANSWER_PAGES_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for pdf_page in dict.fromkeys(pdf_pages):
        page_index = int(pdf_page) - 1
        if page_index < 0 or page_index >= len(doc):
            raise ValueError(
                f"PDF page {pdf_page} is outside the source document"
            )
        filename = f"{source_slug}_source_p{page_index:03d}.jpg"
        output_path = ANSWER_PAGES_DIR / filename
        if not output_path.exists():
            pix = doc[page_index].get_pixmap(
                matrix=fitz.Matrix(2.0, 2.0), alpha=False
            )
            if pix.colorspace and pix.colorspace.n > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(str(output_path), jpg_quality=92)
        paths.append(f"data/crops/original_answer_pages/{filename}")
    return paths


def backfill_cfm_original_answer_pages(
    case_id: int,
    pdf_path: str | Path,
    backup_dir: str | Path,
) -> tuple[int, int, Path]:
    """Backfill full cited source spreads for an already imported CFM session."""
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"edir_prep.before_cfm_source_pages_{stamp}.db"
    shutil.copy2(DB_PATH, backup_path)
    init_db()

    pdf_path = Path(pdf_path)
    if not pdf_path.is_file():
        raise FileNotFoundError(pdf_path)
    with get_conn() as conn:
        case = conn.execute(
            "SELECT id, source, library_key FROM cases WHERE id=?", (case_id,)
        ).fetchone()
        if not case or case["library_key"] != LIBRARY_UEFA_CFM:
            raise ValueError(f"Case {case_id} is not a UEFA CFM session")
        questions = conn.execute(
            "SELECT id, source_locator FROM questions WHERE case_id=? "
            "ORDER BY q_number",
            (case_id,),
        ).fetchall()

    source_slug = f"cfm_{_slug(case['source'], 50)}"
    rendered: dict[int, list[str]] = {}
    unique_pages: set[int] = set()
    with fitz.open(pdf_path) as doc:
        for question in questions:
            locator = json.loads(question["source_locator"] or "{}")
            if locator.get("file") != pdf_path.name:
                raise ValueError(
                    f"Question {question['id']} cites {locator.get('file')!r}, "
                    f"not {pdf_path.name!r}"
                )
            pdf_pages = locator.get("pdf_pages") or []
            unique_pages.update(pdf_pages)
            rendered[question["id"]] = _render_original_source_pages(
                pdf_pages, doc, source_slug
            )

    with get_conn() as conn:
        for question_id, paths in rendered.items():
            conn.execute(
                "UPDATE questions SET original_answer_pages=? WHERE id=?",
                (json.dumps(paths, ensure_ascii=False), question_id),
            )
    return len(rendered), len(unique_pages), backup_path


def import_approved_session(
    payload: dict,
    pdf_path: str | Path,
    backup_dir: str | Path,
) -> tuple[int, int, Path]:
    errors = validate_session(payload, pdf_path)
    if errors:
        raise ValueError("\n".join(errors))

    init_db()
    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"edir_prep.before_cfm_{stamp}.db"
    shutil.copy2(DB_PATH, backup_path)

    pdf_path = Path(pdf_path)
    source_slug = f"cfm_{_slug(payload['session_title'], 50)}"
    rendered: dict[int, tuple[list[str], list[str], list[str]]] = {}
    CROPS_DIR.mkdir(parents=True, exist_ok=True)
    if fitz is None:
        raise RuntimeError("PyMuPDF is required for CFM imports")
    with fitz.open(pdf_path) as doc:
        for question in payload["questions"]:
            image_paths, captions = _resolve_page_crops(
                question.get("page_crops") or [], doc, source_slug
            )
            source_pages = _render_original_source_pages(
                question["source_locator"]["pdf_pages"], doc, source_slug
            )
            rendered[int(question["q_number"])] = (
                image_paths,
                captions,
                source_pages,
            )

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM cases WHERE library_key=? AND source=?",
            (LIBRARY_UEFA_CFM, payload["session_title"]),
        ).fetchone()
        if existing:
            raise ValueError(
                f"A UEFA CFM session named {payload['session_title']!r} already exists"
            )
        chapter = conn.execute(
            "SELECT id FROM chapters WHERE number=?", (CFM_CHAPTER_NUMBER,)
        ).fetchone()
        if not chapter:
            conn.execute(
                "INSERT INTO chapters (number, title) VALUES (?, ?)",
                (CFM_CHAPTER_NUMBER, CFM_CHAPTER_TITLE),
            )
            chapter_id = conn.execute(
                "SELECT id FROM chapters WHERE number=?", (CFM_CHAPTER_NUMBER,)
            ).fetchone()[0]
        else:
            chapter_id = chapter[0]
        case_number = conn.execute(
            "SELECT COALESCE(MAX(case_number), 0) + 1 FROM cases "
            "WHERE chapter_id=? AND section='mrq' AND library_key=?",
            (chapter_id, LIBRARY_UEFA_CFM),
        ).fetchone()[0]
        case_cursor = conn.execute(
            """INSERT INTO cases
               (chapter_id, case_number, section, clinical_vignette, source,
                chapter_match, library_key)
               VALUES (?, ?, 'mrq', '', ?, 'exact', ?)""",
            (
                chapter_id,
                case_number,
                payload["session_title"],
                LIBRARY_UEFA_CFM,
            ),
        )
        case_id = case_cursor.lastrowid
        for question in payload["questions"]:
            q_number = int(question["q_number"])
            image_paths, captions, original_answer_pages = rendered[q_number]
            q_cursor = conn.execute(
                """INSERT INTO questions
                   (case_id, q_number, question_text, q_type, options, page_images,
                    page_image_captions, source_locator, original_answer_pages)
                   VALUES (?, ?, ?, 'multiple_choice', ?, ?, ?, ?, ?)""",
                (
                    case_id,
                    q_number,
                    question["question_text"],
                    json.dumps(question["options"], ensure_ascii=False),
                    json.dumps(image_paths, ensure_ascii=False),
                    json.dumps(captions, ensure_ascii=False),
                    json.dumps(question["source_locator"], ensure_ascii=False),
                    json.dumps(original_answer_pages, ensure_ascii=False),
                ),
            )
            answer = question["answer"]
            conn.execute(
                """INSERT INTO answers
                   (question_id, answer_text, correct_options, explanation, page_images)
                   VALUES (?, '', ?, ?, '[]')""",
                (
                    q_cursor.lastrowid,
                    json.dumps(answer["correct_options"]),
                    answer["explanation"],
                ),
            )
    return case_id, len(payload["questions"]), backup_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path")
    parser.add_argument("pdf_path")
    parser.add_argument(
        "--import-approved",
        action="store_true",
        help="Import after validation; omit for a read-only validation audit.",
    )
    parser.add_argument(
        "--backup-dir",
        default=str(Path(DB_PATH).parent.parent.parent / "backups" / "CFM"),
    )
    args = parser.parse_args()
    payload = load_payload(args.json_path)
    errors = validate_session(payload, args.pdf_path)
    if errors:
        print(json.dumps({"valid": False, "errors": errors}, indent=2))
        raise SystemExit(1)
    print(json.dumps({"valid": True, "audit": audit_session(payload)}, indent=2))
    if args.import_approved:
        case_id, count, backup = import_approved_session(
            payload, args.pdf_path, args.backup_dir
        )
        print(f"Imported case {case_id} with {count} questions")
        print(f"Database backup: {backup}")


if __name__ == "__main__":
    main()
