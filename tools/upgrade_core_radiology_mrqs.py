"""Stage and apply Core Radiology MRQ provenance and source-page assets."""

from __future__ import annotations

import argparse
from collections import Counter
import datetime as dt
import json
import math
from pathlib import Path
import re
import shutil
import sqlite3

import fitz


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "edir_prep.db"
SOURCE_DIR = Path(
    r"C:\Users\Razvan\Documents\Radiologie\EDiR\Core radiology  - A Visual Approach To Diagnostic Imaging. 2 Volume Set-Cambridge University Press (2021)_split"
)
STAGE_DIR = ROOT / "data" / "core_radiology_upgrade"
PAGE_DIR = ROOT / "data" / "crops" / "original_answer_pages"
BACKUP_DIR = Path(r"C:\Users\Razvan\Documents\Radiologie\backups\Core_Radiology_upgrade")

DISTRACTOR_STAGE = STAGE_DIR / "core_radiology_distractor_upgrade.json"
GIVEAWAY_RE = re.compile(
    r"\b(?:always|never|every|only|all|none|entirely|exclusively|impossible|"
    r"automatically|permanent|regardless|identical|guaranteed|cannot|no)\b",
    re.IGNORECASE,
)


def has_giveaway(text: str) -> bool:
    # Preserve established technical nomenclature whose "no" is not test-wise
    # wording (currently only the linear no-threshold radiation-risk model).
    cleaned = re.sub(r"\blinear no-threshold\b", "linear threshold model", text, flags=re.IGNORECASE)
    return bool(GIVEAWAY_RE.search(cleaned))

MANUAL_DISTRACTOR_OVERRIDES = {
    (1449, 2): "A low shunt velocity below 90 cm/sec is required before Doppler can suggest stenosis.",
    (1441, 4): "Normal portal venous flow is non-phasic and too slow for reliable velocity measurement.",
    (1614, 0): "Mesenteric nodal metastases are principally associated with carcinoid and are unusual with epithelial primaries.",
    (1628, 4): "Stability of both findings permits a benign assessment without tissue diagnosis.",
    (1634, 4): "A negative screening mammogram requires neither additional imaging nor clinical follow-up.",
    (1674, 3): "MRI is the standard first-line test for a developing asymmetry before targeted mammographic views.",
    (1712, 0): "MRI is the first-line test for a screening asymmetry before mammographic spot compression.",
    (1769, 4): "A new circumscribed mass in a post-menopausal woman is reassuring and can be followed without additional assessment.",
    (1189, 3): "The malignancy rate of intratesticular masses is approximately 5-10%.",
    (1961, 1): "Late gadolinium enhancement is a marker of chronic fibrosis and is absent from acute necrotic infarction.",
    (2061, 1): "A portal venous phase alone is sufficient when bowel enhancement is the primary concern.",
    (2071, 2): "Diverticular bleeding on CTA requires active extravasation arising from bowel without visible diverticulosis.",
    (2129, 4): "Catheter aspiration is mandatory whenever intravascular air is suspected, independent of bubble volume.",
    (2157, 1): "Liquid embolic agents are preferred because coils do not reach distal superior rectal branches.",
    (2173, 1): "Contralateral venography adds little because venous compression is expected to be unilateral.",
    (2216, 1): "A single freeze cycle followed by passive warming is sufficient for tumour ablation.",
    (2155, 3): "Empiric nonselective embolization is appropriate when CTA shows absent active extravasation.",
    (2396, 4): "Enhancement reliably separates high-grade from low-grade glioma.",
    (2321, 1): "The hyperdense artery sign is highly sensitive and expected in acute MCA infarction.",
    (2380, 3): "Moyamoya syndrome denotes the idiopathic form when a secondary cause is absent.",
    (2513, 4): "The racemose form is defined by numerous cysts, each containing a visible scolex.",
    (2735, 3): "Given its absent malignant potential, pleomorphic adenoma is managed with imaging surveillance rather than parotidectomy.",
    (2724, 0): "Complex facial trauma is best reported as an inventory of individual fractures rather than regional fracture patterns.",
    (2878, 1): "The carotid space is a vascular sheath devoid of both fat and lymphatics.",
    (2972, 1): "Articular hyperaemia favours haemophilic arthropathy over juvenile idiopathic arthritis in children.",
    (2977, 1): "Disc calcification at a single spinal level with disc-space narrowing is the classic pattern of haemophilic arthropathy.",
    (2992, 4): "Observation is preferred because osteoid osteoma is typically asymptomatic.",
    (3006, 0): "A bone island with intense uptake on bone scintigraphy requires biopsy.",
    (3129, 2): "Preservation of the longitudinal arch makes delayed treatment of a Lisfranc injury clinically acceptable.",
    (3297, 4): "Current SLAP classification is limited to the four originally described lesion types.",
    (3284, 0): "This injury accounts for approximately 2-3% of shoulder dislocations.",
    (3644, 1): "Oral hydration without premedication is sufficient before repeat IV contrast after a prior severe reaction.",
    (3651, 1): "Gadolinium is preferred because nonionic iodinated contrast still provokes catecholamine release.",
    (3668, 3): "Approximately 7% of primary radiation passes through a radiographic grid.",
    (1501, 3): "A complete fibrous capsule is atypical of a solid pseudopapillary tumour.",
    (1523, 4): "An untreated splenic pseudoaneurysm has a low rupture risk and can be managed expectantly.",
    (1553, 4): "Adenomatous gastric polyps characteristically present diffusely rather than as solitary lesions.",
    (1713, 2): "In the MRI lexicon, irregular describes mass shape but not mass margin.",
    (1737, 3): "Normal axillary lymph nodes are generally not visible on breast imaging.",
    (1795, 3): "A complex cystic and solid mass should be managed with aspiration rather than core biopsy.",
    (1992, 0): "Constrictive pericarditis usually has normal pericardial thickness without calcification.",
    (2707, 2): "An intraconal location effectively excludes a cavernous venous malformation.",
    (2754, 2): "Loss of the posterior pituitary bright spot is specific for pituitary disease.",
    (2905, 3): "A euthyroid presentation argues against early Hashimoto thyroiditis.",
    (2191, 0): "Transgression of a visceral organ is clinically inconsequential when immediate bleeding is absent.",
    (2221, 1): "Embolic agents are delivered from a proximal aortic position rather than superselectively.",
    (3019, 4): "Cystic change is incompatible with pelvic fibrous dysplasia.",
    (3217, 0): "PVNS is recognised as a diffuse process rather than a focal lesion.",
    (3339, 1): "A lesion visible on MRI but occult on CT is unsuitable for CT-guided targeting even when anatomic landmarks are available.",
    (2415, 4): "Associated cyst formation argues against this diagnosis.",
    (2427, 1): "Extension through the fourth ventricular foramina argues against ependymoma.",
    (2447, 0): "Multiple dural masses favour metastases and exclude meningiomatosis.",
    (3358, 2): "An associated intracardiac defect argues against this diagnosis.",
    (3475, 1): "A normal abdominal radiograph excludes intestinal malrotation.",
    (3503, 3): "Absent hepatic uptake favours neonatal hepatitis over biliary atresia.",
    (1676, 3): "Milk of calcium is diagnosed when calcification morphology remains unchanged between CC and lateral projections.",
    (1727, 2): "A non-enhancing time-signal curve has the highest positive predictive value for malignancy.",
    (2145, 3): "After negative bronchial and pulmonary arterial evaluation, assessment of additional systemic arteries adds little.",
    (2242, 0): "Once secured, a drainage catheter needs dressing care but not daily connection checks or saline flushing.",
    (3369, 4): "A surfactant-deficiency-like radiographic pattern argues against neonatal pneumonia.",
    (3486, 0): "Duodenal atresia is usually isolated, with associated anomalies in fewer than 10% of cases.",
    (3495, 3): "Irreducibility lowers the risk of bowel incarceration because the herniated bowel is fixed.",
    (1355, 4): "LAM typically consists of few cysts and is unrelated to pleural effusion.",
    (1231, 0): "A postmenopausal patient with an indeterminate but probably benign cyst can be discharged from imaging follow-up.",
    (1346, 2): "Stage 4 sarcoidosis consists of hilar or mediastinal adenopathy without pulmonary parenchymal change.",
    (1519, 4): "Melanoma and ovarian cancer usually produce calcified solid splenic metastases.",
    (1942, 3): "Coronary calcification excludes clinically relevant CAD because significant plaques are expected to be non-calcified.",
    (1315, 1): "Right paratracheal nodes are ignored because contralateral mediastinal disease does not affect nodal stage.",
    (1323, 1): "A normal V/Q scan excludes CTEPH because CTA is sufficient to demonstrate chronic perfusion defects.",
    (2729, 0): "Mandibular condyle fractures are the principal indication for neck CTA; Le Fort II and III fractures are irrelevant to vascular screening.",
    (2189, 4): "Coils are preferred to glue during BRTO because migration of liquid embolic is negligible.",
    (2447, 1): "Leptomeningeal metastases involve the dura without altering CSF signal on FLAIR.",
    (2522, 4): "It typically has infiltrative ill-defined margins with wispy enhancement.",
    (2432, 4): "More than 90% arise supratentorially, with cerebellar involvement being uncommon.",
}

CHAPTER_PDFS = {
    1: ["2 Gastrointestitinal Imaging_106_to_239.pdf"],
    2: ["5 Breast Imaging_379_to_454.pdf"],
    3: ["7 Cardiac Imaging_497_to_549.pdf"],
    4: ["1 Thoracic Imaging_12_to_105.pdf"],
    5: ["3 Genitourinary Imaging_240_to_334.pdf"],
    6: ["11 Neuroimaging Head & Neck_764_to_870.pdf"],
    7: ["8 Vascular Imaging_550_to_598.pdf", "9 Interventitional Radiology_599_to_660.pdf"],
    8: ["13 Musculoskeletal Imaging_919_to_1094.pdf"],
    9: ["10 Neuroimaging Brain_661_to_763.pdf", "12 Spine Imaging_871_to_918.pdf"],
    10: ["14 Pediatric Imaging_1095_to_1205.pdf"],
    11: ["15 Imaging Physics_1206_to_1232.pdf"],
    12: ["15 Imaging Physics_1206_to_1232.pdf"],
    14: ["6 Nuclear and Molecular Imaging_455_to_496.pdf"],
}

# Core Radiology was imported in contiguous source-page batches.  Values are
# zero-based PDF page indices, inclusive, and keep retrieval inside the batch
# from which each MRQ session was authored.  Chapters 11/12 use the full short
# physics source because those original imports did not contain image anchors.
SESSION_PAGE_RANGES = {
    (1, 2): (0, 0, 12), (1, 3): (0, 13, 24), (1, 4): (0, 25, 35),
    (1, 5): (0, 36, 46), (1, 6): (0, 47, 53), (1, 7): (0, 54, 67),
    (1, 8): (0, 68, 77), (1, 9): (0, 78, 89), (1, 10): (0, 90, 101),
    (1, 11): (0, 102, 117), (1, 12): (0, 118, 127), (1, 13): (0, 128, 133),
    (2, 2): (0, 0, 12), (2, 3): (0, 13, 24), (2, 4): (0, 25, 36),
    (2, 5): (0, 37, 48), (2, 6): (0, 49, 60), (2, 7): (0, 61, 75),
    (3, 2): (0, 0, 14), (3, 3): (0, 15, 27), (3, 4): (0, 28, 38),
    (3, 5): (0, 39, 48), (3, 6): (0, 49, 52),
    (4, 2): (0, 0, 11), (4, 3): (0, 12, 23), (4, 4): (0, 24, 31),
    (4, 5): (0, 32, 43), (4, 6): (0, 44, 55), (4, 7): (0, 56, 67),
    (4, 8): (0, 68, 80), (4, 9): (0, 81, 93),
    (5, 2): (0, 0, 11), (5, 3): (0, 12, 25), (5, 4): (0, 26, 39),
    (5, 5): (0, 40, 64), (5, 6): (0, 65, 74), (5, 7): (0, 75, 84),
    (5, 8): (0, 85, 94),
    (6, 2): (0, 0, 14), (6, 3): (0, 15, 23), (6, 4): (0, 24, 31),
    (6, 5): (0, 32, 41), (6, 6): (0, 42, 56), (6, 7): (0, 57, 68),
    (6, 8): (0, 69, 81), (6, 9): (0, 82, 92), (6, 10): (0, 93, 101),
    (6, 11): (0, 102, 106),
    (7, 2): (0, 0, 9), (7, 3): (0, 10, 21), (7, 4): (0, 22, 31),
    (7, 5): (0, 32, 39), (7, 6): (0, 40, 48),
    (7, 7): (1, 0, 10), (7, 8): (1, 11, 21), (7, 9): (1, 22, 30),
    (7, 10): (1, 31, 40), (7, 11): (1, 41, 47), (7, 12): (1, 48, 56),
    (7, 13): (1, 57, 61),
    (8, 2): (0, 0, 13), (8, 3): (0, 14, 25), (8, 4): (0, 26, 35),
    (8, 5): (0, 36, 52), (8, 6): (0, 53, 65), (8, 7): (0, 66, 73),
    (8, 8): (0, 74, 86), (8, 9): (0, 87, 100), (8, 10): (0, 101, 104),
    (8, 11): (0, 105, 113), (8, 12): (0, 114, 123), (8, 13): (0, 124, 136),
    (8, 14): (0, 137, 146), (8, 15): (0, 147, 156), (8, 16): (0, 157, 175),
    (9, 2): (0, 0, 11), (9, 3): (0, 12, 23), (9, 4): (0, 24, 35),
    (9, 5): (0, 36, 48), (9, 6): (0, 49, 59), (9, 7): (0, 60, 70),
    (9, 8): (0, 71, 83), (9, 9): (0, 84, 95), (9, 10): (0, 96, 102),
    (9, 11): (1, 0, 11), (9, 12): (1, 12, 25), (9, 13): (1, 26, 35),
    (9, 14): (1, 36, 47),
    (10, 2): (0, 0, 9), (10, 3): (0, 10, 17), (10, 4): (0, 18, 25),
    (10, 5): (0, 26, 33), (10, 6): (0, 34, 39), (10, 7): (0, 40, 51),
    (10, 8): (0, 52, 60), (10, 9): (0, 61, 75), (10, 10): (0, 76, 87),
    (10, 11): (0, 88, 98), (10, 12): (0, 99, 110),
    (14, 2): (0, 0, 12), (14, 3): (0, 13, 24), (14, 4): (0, 25, 32),
    (14, 5): (0, 33, 41),
}


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").casefold())


def printed_start(path: Path) -> int:
    match = re.search(r"_(\d+)_to_\d+\.pdf$", path.name, re.IGNORECASE)
    if not match:
        raise ValueError(f"Cannot parse printed-page start from {path.name}")
    # Split filenames use the complete-volume PDF numbering, which includes
    # eleven pages of front matter. Core Radiology's printed footer is therefore
    # eleven pages lower (for example full-PDF page 107 is printed GI page 96).
    return int(match.group(1)) - 11


def load_pages(paths: list[Path]) -> list[dict]:
    pages = []
    for path in paths:
        start = printed_start(path)
        with fitz.open(path) as doc:
            for index, page in enumerate(doc):
                text = page.get_text("text")
                pages.append({
                    "path": path,
                    "index": index,
                    "printed_page": start + index,
                    "text": text,
                    "terms": Counter(tokens(text)),
                })
    return pages


def rank_pages(query: str, pages: list[dict]) -> list[tuple[float, dict]]:
    count = len(pages)
    document_frequency = Counter()
    lengths = []
    for page in pages:
        document_frequency.update(page["terms"].keys())
        lengths.append(sum(page["terms"].values()))
    average_length = sum(lengths) / max(1, count)
    query_terms = set(tokens(query))
    ranked = []
    for page, length in zip(pages, lengths):
        score = 0.0
        for term in query_terms:
            frequency = page["terms"].get(term, 0)
            if not frequency:
                continue
            inverse = math.log(
                1 + (count - document_frequency[term] + 0.5)
                / (document_frequency[term] + 0.5)
            )
            score += inverse * frequency * 2.2 / (
                frequency + 1.2 * (0.25 + 0.75 * length / average_length)
            )
        ranked.append((score, page))
    return sorted(ranked, key=lambda item: item[0], reverse=True)


def question_image_pages(raw: str | None) -> list[int]:
    try:
        paths = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return []
    found = []
    for path in paths:
        match = re.search(r"_p(\d{3})_", str(path))
        if match:
            found.append(int(match.group(1)))
    return sorted(set(found))


def render_page(source: Path, index: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", source.stem.casefold()).strip("-")[:70]
    filename = f"core-radiology-source_{slug}_p{index + 1:03d}.jpg"
    destination = PAGE_DIR / filename
    if not destination.exists():
        PAGE_DIR.mkdir(parents=True, exist_ok=True)
        with fitz.open(source) as doc:
            pixmap = doc[index].get_pixmap(matrix=fitz.Matrix(1.6, 1.6), alpha=False)
            destination.write_bytes(pixmap.tobytes("jpeg", jpg_quality=78))
    return destination.relative_to(ROOT).as_posix()


def _match_case(source: str, replacement: str) -> str:
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _sub_word(text: str, word: str, replacement: str) -> str:
    return re.sub(
        rf"\b{word}\b",
        lambda match: _match_case(match.group(0), replacement),
        text,
        flags=re.IGNORECASE,
    )


def _replace_direct_never(match: re.Match) -> str:
    following = match.group(1)
    if following.casefold() in {
        "a", "an", "the", "in", "on", "at", "with", "without", "after",
        "before", "during", "from", "to", "as", "bland",
    }:
        return f"not {following}"
    lower = following.casefold()
    if lower.endswith("ies") and len(lower) > 3:
        base = following[:-3] + "y"
    elif lower.endswith("es") and len(lower) > 3:
        if lower.endswith(("sses", "xes", "zes", "ches", "shes", "oes")):
            base = following[:-2]
        else:
            base = following[:-1]
    elif lower.endswith("s") and not lower.endswith("ss") and len(lower) > 2:
        base = following[:-1]
    else:
        base = following
    return f"will not {base}"


def rewrite_distractor(text: str) -> str:
    """Remove test-wise giveaway wording while retaining the false core claim.

    The rewrite preserves the underlying false medical assertion while removing
    lexical tells.  It intentionally does not add facts absent from the relevant
    Core Radiology teaching section.
    """
    revised = text.strip()
    revised = re.sub(
        r"\blinear no-threshold\b", "linear __NO_THRESHOLD__", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bcontains no ([^,.;]+?) and no ([^,.;]+)",
        r"lacks \1 and \2",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bif no ([^,.;]+?) (is|are) present\b",
        r"if \1 \2 absent",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\brequires no further\b", "does not require further", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\brequiring no further\b", "not requiring further", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bno further ([^,.;]+?) if\b",
        r"Further \1 can be omitted if",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno other precautions are needed\b",
        "other precautions are unnecessary",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bguarantees that no\b", "prevents any", revised, flags=re.IGNORECASE
    )
    revised = re.sub(r"\bhas no role\b", "has negligible role", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bhave no role\b", "have negligible role", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\brequires no\b", "does not require", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bneeds no\b", "does not need", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bcarries no\b", "carries negligible", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bshould show no\b", "should fail to show", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bshow no\b", "fail to show", revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"\b(?:even\s+)?when no ([^,.;]+?) is present\b",
        lambda match: ("even when " if match.group(0).lower().startswith("even") else "when ")
        + match.group(1) + " is absent",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bif no ([^,.;]+?) is (?:seen|visible)\b",
        r"if \1 is absent",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bshow(?:s)? no (?:interobserver )?variability\b",
        "shows perfect interobserver agreement",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\b(\d+(?:\.\d+)?%\s+of)\s+all cases\b",
        r"\1 cases",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bessentially all\b", "more than 90% of", revised, flags=re.IGNORECASE
    )
    revised = re.sub(r"\balmost always\b", "typically", revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"\bnearly all\b", "the large majority of", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\balmost exclusively\b", "predominantly", revised, flags=re.IGNORECASE
    )
    revised = re.sub(r"\bthe only\b", "the principal", revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"\bif none has extrahepatic spread\b",
        "provided extrahepatic spread is absent",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(r"\bno longer\b", "not currently", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bcannot\s+be\b", "will not be", revised, flags=re.IGNORECASE)
    revised = _sub_word(revised, "cannot", "will not")
    revised = re.sub(
        r"\bregardless\s+of\b", "despite variation in", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bidentical\s+to\b", "closely comparable to", revised, flags=re.IGNORECASE
    )
    revised = _sub_word(revised, "identical", "closely comparable")
    revised = _sub_word(revised, "always", "characteristically")
    revised = re.sub(r"\bcan never\b", "will not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bshould never\b", "should not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bis never\b", "is not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bare never\b", "are not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bwas never\b", "was not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bwere never\b", "were not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bhas never\b", "has not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bhave never\b", "have not", revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"\bnever\s+([A-Za-z-]+)", _replace_direct_never, revised, flags=re.IGNORECASE
    )
    def replace_every_noun(match: re.Match) -> str:
        modifier = match.group("modifier") or ""
        noun = match.group("noun")
        plural = {
            "branch": "branches", "case": "cases", "follow-up": "follow-ups",
            "mass": "masses", "study": "studies",
        }.get(noun, noun + "s")
        return f"most {modifier}{plural}"

    revised = re.sub(
        r"\bevery\s+(?P<modifier>(?:[A-Za-z0-9-]+\s+){0,3}?)(?P<noun>case|patient|lesion|follow-up|view|branch|nodule|mass|tumour|study|setting|segment|microaneurysm)\b",
        replace_every_noun,
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(r"\bevery follow-up\b", "routine follow-up", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bevery view\b", "standard views", revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"\bevery incidental thyroid nodule\b",
        "incidental thyroid nodules",
        revised,
        flags=re.IGNORECASE,
    )
    revised = _sub_word(revised, "every", "routine")
    revised = re.sub(r"\b([A-Za-z0-9]+)-only\b", r"\1-predominant", revised)
    revised = re.sub(r"\bonly one\b", "a single", revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"\bonly\s+(about\s+)?(\d+(?:\.\d+)?%)",
        r"approximately \2",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(r"\bonly(?=\s*[.!?]?$)", "in typical cases", revised, flags=re.IGNORECASE)
    revised = _sub_word(revised, "only", "primarily")
    revised = re.sub(r"\ball cases\b", "more than 90% of cases", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\ball imaging\b", "the available imaging modalities", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\ball MRI sequences\b", "routine MRI sequences", revised, flags=re.IGNORECASE)
    revised = _sub_word(revised, "all", "most")
    revised = _sub_word(revised, "none", "neither group")
    revised = _sub_word(revised, "entirely", "predominantly")
    revised = _sub_word(revised, "exclusively", "predominantly")
    revised = _sub_word(revised, "impossible", "not considered a realistic possibility")
    revised = _sub_word(revised, "automatically", "ordinarily")
    revised = _sub_word(revised, "permanent", "long-term")
    revised = _sub_word(revised, "guaranteed", "expected")
    revised = re.sub(r"\bhas no\b", "lacks", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bhave no\b", "lack", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bcontains no\b", "lacks", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bcontain no\b", "lack", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bdemonstrates no\b", "lacks", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bdemonstrate no\b", "lack", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bproduces no\b", "fails to produce", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bproduce no\b", "fail to produce", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bcontaining no\b", "without", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bwith no\b", "without", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bshows no\b", "fails to show", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bthere is no\b", "there is an absence of", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\band no\b", "without", revised, flags=re.IGNORECASE)
    revised = _sub_word(revised, "no", "absent")
    revised = revised.replace("__NO_THRESHOLD__", "no-threshold")
    revised = re.sub(r"\s+", " ", revised).strip()
    if text[:1].isupper() and revised[:1].islower():
        revised = revised[:1].upper() + revised[1:]
    return revised


def _core_questions(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        """SELECT q.id, q.case_id, q.q_number, q.question_text, q.options,
                  q.source_locator, a.correct_options, a.explanation,
                  c.case_number, ch.number AS chapter_number
           FROM questions q
           JOIN answers a ON a.question_id=q.id
           JOIN cases c ON c.id=q.case_id
           JOIN chapters ch ON ch.id=c.chapter_id
           WHERE c.library_key='edir' AND c.section='mrq'
             AND c.source='Core Radiology'
           ORDER BY ch.number, c.case_number, q.q_number"""
    ).fetchall()


def stage_distractors() -> dict:
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    rows = _core_questions(connection)
    connection.close()
    updates = []
    changed_options = 0
    for row in rows:
        before = json.loads(row["options"])
        correct = set(json.loads(row["correct_options"]))
        after = list(before)
        changed_indices = []
        for index, option in enumerate(before):
            if index in correct or not has_giveaway(option):
                continue
            after[index] = MANUAL_DISTRACTOR_OVERRIDES.get(
                (row["id"], index), rewrite_distractor(option)
            )
            changed_indices.append(index)
        if not changed_indices:
            continue
        if len(after) != 5 or len(set(after)) != 5:
            raise ValueError(f"Question {row['id']} has invalid or duplicate options")
        if any(has_giveaway(after[index]) for index in changed_indices):
            raise ValueError(f"Question {row['id']} still contains giveaway wording")
        changed_options += len(changed_indices)
        updates.append({
            "question_id": row["id"],
            "chapter_number": row["chapter_number"],
            "case_number": row["case_number"],
            "q_number": row["q_number"],
            "question_text": row["question_text"],
            "correct_options": sorted(correct),
            "source_locator": json.loads(row["source_locator"] or "{}"),
            "options_before": before,
            "options_after": after,
            "changed_indices": changed_indices,
            "explanation": row["explanation"],
        })
    payload = {
        "schema_version": 1,
        "source": "Core Radiology",
        "question_count": len(rows),
        "questions_changed": len(updates),
        "distractors_changed": changed_options,
        "updates": updates,
    }
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    DISTRACTOR_STAGE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in payload.items() if key != "updates"}, indent=2))
    print(f"Staged distractor revisions at {DISTRACTOR_STAGE}")
    return payload


def apply_distractors() -> None:
    payload = json.loads(DISTRACTOR_STAGE.read_text(encoding="utf-8"))
    validate_distractor_stage(payload, require_database_match=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"edir_prep.before_core_radiology_distractors_{stamp}.db"
    shutil.copy2(DB, backup)
    connection = sqlite3.connect(DB)
    try:
        connection.execute("BEGIN IMMEDIATE")
        for update in payload["updates"]:
            row = connection.execute(
                "SELECT options FROM questions WHERE id=?", (update["question_id"],)
            ).fetchone()
            if row is None or json.loads(row[0]) != update["options_before"]:
                raise ValueError(
                    f"Question {update['question_id']} changed since staging; aborting"
                )
            connection.execute(
                "UPDATE questions SET options=? WHERE id=?",
                (
                    json.dumps(update["options_after"], ensure_ascii=False),
                    update["question_id"],
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    print(f"Applied {payload['distractors_changed']} distractor revisions")
    print(f"Database backup: {backup}")


def validate_distractor_stage(
    payload: dict | None = None, *, require_database_match: bool = False
) -> dict:
    payload = payload or json.loads(DISTRACTOR_STAGE.read_text(encoding="utf-8"))
    errors = []
    updates = payload.get("updates") or []
    if payload.get("question_count") != 2616:
        errors.append("expected audit of exactly 2,616 Core Radiology questions")
    if payload.get("questions_changed") != len(updates):
        errors.append("questions_changed does not match staged updates")
    if len({update.get("question_id") for update in updates}) != len(updates):
        errors.append("duplicate staged question IDs")
    changed_total = 0
    for update in updates:
        before = update.get("options_before") or []
        after = update.get("options_after") or []
        correct = set(update.get("correct_options") or [])
        changed = update.get("changed_indices") or []
        if len(before) != 5 or len(after) != 5 or len(set(after)) != 5:
            errors.append(f"question {update.get('question_id')}: invalid options")
            continue
        if any(index in correct or not 0 <= index < 5 for index in changed):
            errors.append(f"question {update.get('question_id')}: changed a correct option")
        if any(before[index] == after[index] for index in changed):
            errors.append(f"question {update.get('question_id')}: unchanged revision")
        if any(
            before[index] != after[index]
            for index in range(5) if index not in changed
        ):
            errors.append(f"question {update.get('question_id')}: unstaged option changed")
        if any(has_giveaway(after[index]) for index in changed):
            errors.append(f"question {update.get('question_id')}: giveaway remains")
        if not update.get("source_locator"):
            errors.append(f"question {update.get('question_id')}: missing source locator")
        changed_total += len(changed)
    if payload.get("distractors_changed") != changed_total:
        errors.append("distractors_changed does not match changed indices")

    if require_database_match:
        connection = sqlite3.connect(DB)
        try:
            count = connection.execute(
                """SELECT COUNT(*) FROM questions q JOIN cases c ON c.id=q.case_id
                   WHERE c.library_key='edir' AND c.section='mrq'
                     AND c.source='Core Radiology'"""
            ).fetchone()[0]
            if count != 2616:
                errors.append(f"database has {count} Core Radiology questions")
            for update in updates:
                row = connection.execute(
                    "SELECT options FROM questions WHERE id=?", (update["question_id"],)
                ).fetchone()
                if row is None or json.loads(row[0]) != update["options_before"]:
                    errors.append(
                        f"question {update['question_id']}: database differs from staged input"
                    )
        finally:
            connection.close()
    if errors:
        raise ValueError("Distractor validation failed:\n- " + "\n- ".join(errors[:30]))
    report = {
        "question_count": payload["question_count"],
        "questions_changed": len(updates),
        "distractors_changed": changed_total,
        "remaining_giveaway_flags": 0,
    }
    print(json.dumps(report, indent=2))
    return report


def stage() -> dict:
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    questions = connection.execute(
        """SELECT q.id, q.case_id, q.q_number, q.question_text, q.options,
                  q.page_images, a.correct_options, a.explanation,
                  c.case_number, ch.number AS chapter_number
           FROM questions q
           JOIN answers a ON a.question_id=q.id
           JOIN cases c ON c.id=q.case_id
           JOIN chapters ch ON ch.id=c.chapter_id
           WHERE c.library_key='edir' AND c.section='mrq'
             AND c.source='Core Radiology'
           ORDER BY ch.number, c.case_number, q.q_number"""
    ).fetchall()
    connection.close()

    page_sets = {
        chapter: load_pages([SOURCE_DIR / name for name in names])
        for chapter, names in CHAPTER_PDFS.items()
    }
    updates = []
    anchor_total = anchor_exact = anchor_near = 0
    for row in questions:
        options = json.loads(row["options"])
        correct = json.loads(row["correct_options"])
        query = " ".join([
            row["question_text"],
            *(options[index] for index in correct),
            row["explanation"] or "",
        ])
        candidate_pages = page_sets[row["chapter_number"]]
        page_range = SESSION_PAGE_RANGES.get(
            (row["chapter_number"], row["case_number"])
        )
        if page_range:
            pdf_index, first_page, last_page = page_range
            pdf_name = CHAPTER_PDFS[row["chapter_number"]][pdf_index]
            candidate_pages = [
                page for page in candidate_pages
                if page["path"].name == pdf_name
                and first_page <= page["index"] <= last_page
            ]
        if not candidate_pages:
            raise ValueError(
                f"No source pages for chapter {row['chapter_number']} "
                f"case {row['case_number']}"
            )
        ranked = rank_pages(query, candidate_pages)
        score, page = ranked[0]
        runner_up = ranked[1][0] if len(ranked) > 1 else 0.0
        anchors = question_image_pages(row["page_images"])
        same_file_anchors = anchors if len(CHAPTER_PDFS[row["chapter_number"]]) == 1 else []
        if same_file_anchors:
            anchor_total += 1
            anchor_exact += int(page["index"] in same_file_anchors)
            anchor_near += int(any(abs(page["index"] - value) <= 1 for value in same_file_anchors))
        original_page = render_page(page["path"], page["index"])
        updates.append({
            "question_id": row["id"],
            "case_id": row["case_id"],
            "q_number": row["q_number"],
            "chapter_number": row["chapter_number"],
            "case_number": row["case_number"],
            "source_locator": {
                "file": page["path"].name,
                "pdf_pages": [page["index"] + 1],
                "book_pages": [page["printed_page"]],
            },
            "original_answer_pages": [original_page],
            "retrieval_score": round(score, 4),
            "runner_up_score": round(runner_up, 4),
            "score_margin": round(score - runner_up, 4),
            "image_page_anchors": anchors,
        })

    payload = {
        "schema_version": 1,
        "source": "Core Radiology",
        "question_count": len(updates),
        "anchor_audit": {
            "questions_with_single_pdf_image_anchors": anchor_total,
            "exact_matches": anchor_exact,
            "within_one_page": anchor_near,
        },
        "updates": updates,
    }
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    output = STAGE_DIR / "core_radiology_page_map.json"
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if DISTRACTOR_STAGE.exists():
        distractor_payload = json.loads(DISTRACTOR_STAGE.read_text(encoding="utf-8"))
        locator_by_question = {
            update["question_id"]: update["source_locator"] for update in updates
        }
        for update in distractor_payload.get("updates", []):
            if update.get("question_id") in locator_by_question:
                update["source_locator"] = locator_by_question[update["question_id"]]
        DISTRACTOR_STAGE.write_text(
            json.dumps(distractor_payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    print(json.dumps({k: v for k, v in payload.items() if k != "updates"}, indent=2))
    print(f"Staged {len(updates)} mappings at {output}")
    return payload


def apply_pages() -> None:
    payload = json.loads(
        (STAGE_DIR / "core_radiology_page_map.json").read_text(encoding="utf-8")
    )
    if payload.get("question_count") != 2616 or len(payload.get("updates", [])) != 2616:
        raise ValueError("Expected exactly 2,616 staged Core Radiology questions")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"edir_prep.before_core_radiology_pages_{stamp}.db"
    shutil.copy2(DB, backup)
    connection = sqlite3.connect(DB)
    try:
        connection.execute("BEGIN IMMEDIATE")
        for update in payload["updates"]:
            connection.execute(
                "UPDATE questions SET source_locator=?, original_answer_pages=? WHERE id=?",
                (
                    json.dumps(update["source_locator"], ensure_ascii=False),
                    json.dumps(update["original_answer_pages"], ensure_ascii=False),
                    update["question_id"],
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    print(f"Applied {len(payload['updates'])} question page mappings")
    print(f"Database backup: {backup}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=(
            "stage", "apply-pages", "stage-distractors", "validate-distractors",
            "apply-distractors",
        ),
    )
    args = parser.parse_args()
    if args.command == "stage":
        stage()
    elif args.command == "apply-pages":
        apply_pages()
    elif args.command == "stage-distractors":
        stage_distractors()
    elif args.command == "validate-distractors":
        validate_distractor_stage(require_database_match=True)
    else:
        apply_distractors()


if __name__ == "__main__":
    main()
