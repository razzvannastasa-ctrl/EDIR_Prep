"""Heuristic imaging-modality tagging for CORE/SC cases.

Modality is not captured anywhere in the source material, and most clinical
vignettes never name it, so tags are inferred from whatever text is
available for a case (vignette, article summary, question text, image
captions, source locators, and answer/explanation text) via keyword
matching. This is deliberately a best-effort heuristic, not a guarantee —
cases with no textual hint end up with an empty tag list and are only
visible when a modality filter is not applied (or is fully unchecked).
"""

from __future__ import annotations

import json
import re

from core.database import get_conn

MODALITIES = ["X-Ray", "GI studies", "CT", "MRI", "US", "Nuclear"]

_PATTERNS: dict[str, list[str]] = {
    "CT": [
        r"\bcts?\b", r"computed tomography", r"\bcta\b", r"ct angiograph",
        r"\bhrct\b", r"ct urogram", r"\bctpa\b", r"ct enterograph",
        r"ct colonograph",
    ],
    "MRI": [
        r"\bmri\b", r"magnetic resonance", r"\bmrcp\b", r"\bmra\b",
        r"mr angiograph", r"t1[- ]weighted", r"t2[- ]weighted",
        r"\bstir\b", r"\bflair\b", r"\bdwi\b", r"diffusion[- ]weighted",
        r"gradient echo", r"fse/tse", r"short[- ]tau",
        r"\bmr\b\s+(?:image|imaging|study|sequence|arthrogra|angiograph)",
    ],
    "US": [
        r"ultrasound", r"sonograph", r"\bdoppler\b", r"echogenic",
        r"\becho\b", r"transvaginal scan", r"transabdominal scan",
        r"duplex (?:scan|study|ultrasound)", r"sonogram",
        r"echocardiogra", r"echotextur",
        r"anatomy scan", r"anomaly scan", r"obstetric scan", r"fetal scan",
    ],
    "Nuclear": [
        r"nuclear medicine", r"scintigraph", r"\bpet\b", r"\bpet-ct\b",
        r"\bspect\b", r"radionuclide", r"technetium", r"\bmibi\b",
        r"bone scan", r"\bvq scan\b", r"ventilation.perfusion",
        r"iodine[- ]131", r"\bhida\b", r"gallium scan",
        r"myocardial perfusion imaging", r"pertechnetate", r"\bmag3\b",
        r"renograph", r"gamma[- ]camera", r"labell?ed white blood cell",
        r"\bin-111\b", r"indium-111",
    ],
    "GI studies": [
        r"barium", r"esophagram", r"oesophagram", r"\benema\b",
        r"small bowel follow-through", r"upper gi series",
        r"upper gastrointestinal (?:series|examination|study|fluoroscop)",
        r"lower gastrointestinal (?:series|examination|study|fluoroscop)",
        r"swallow study", r"defecograph", r"sialogram", r"barium swallow",
        r"barium meal", r"fluoroscop",
    ],
    "X-Ray": [
        r"radiograph", r"plain film", r"x-ray", r"\bxray\b", r"mammograph",
        r"\bap view\b", r"\bpa view\b", r"\blateral view\b", r"\bkub\b",
        r"skeletal survey", r"bone age", r"intravenous urogram",
        r"intravenous pyelogram", r"\bivu\b", r"\bivp\b",
        r"retrograde pyelograph", r"retrograde urethrograph",
        r"\bcystogram\b", r"voiding cystourethrogram", r"\bvcug\b",
        r"hysterosalpingogram", r"\bhsg\b",
        r"digital subtraction angiograph", r"\bdsa\b",
        r"angiograph", r"nephrogram", r"nephrostogram", r"cavogram",
        r"venograph", r"arthrogram",
    ],
}

_COMPILED = {
    tag: [re.compile(p, re.IGNORECASE) for p in patterns]
    for tag, patterns in _PATTERNS.items()
}

# "US"/"T1"/"T2" only mean ultrasound/MRI sequences when capitalised as in
# radiology shorthand; matching them case-insensitively would also catch the
# pronoun "us" and stray tokens, so these run case-sensitive instead.
_CASE_SENSITIVE_PATTERNS = {
    "US": [re.compile(r"\bUS\b")],
    "MRI": [re.compile(r"\bT1\b"), re.compile(r"\bT2\b")],
}


def classify_modalities(text: str) -> list[str]:
    """Return the modality tags whose keywords appear anywhere in text."""
    if not text:
        return []
    tags = []
    for tag, regexes in _COMPILED.items():
        if any(regex.search(text) for regex in regexes):
            tags.append(tag)
    for tag, regexes in _CASE_SENSITIVE_PATTERNS.items():
        if tag not in tags and any(regex.search(text) for regex in regexes):
            tags.append(tag)
    return tags


def _case_text(conn, case_id: int) -> str:
    parts: list[str] = []
    case_row = conn.execute(
        "SELECT clinical_vignette, article_summary FROM cases WHERE id=?",
        (case_id,),
    ).fetchone()
    if case_row:
        parts.extend(filter(None, [case_row["clinical_vignette"], case_row["article_summary"]]))
    rows = conn.execute(
        """SELECT q.question_text, q.page_image_captions, q.source_locator,
                  a.answer_text, a.explanation
           FROM questions q
           LEFT JOIN answers a ON a.question_id = q.id
           WHERE q.case_id=?""",
        (case_id,),
    ).fetchall()
    for row in rows:
        parts.append(row["question_text"] or "")
        if row["page_image_captions"]:
            try:
                parts.append(" ".join(json.loads(row["page_image_captions"])))
            except (TypeError, ValueError):
                pass
        if row["source_locator"]:
            parts.append(str(row["source_locator"]))
        parts.extend(filter(None, [row["answer_text"], row["explanation"]]))
    return " ".join(parts)


def backfill_case_modalities(section: str | None = None) -> dict[str, int]:
    """Recompute and store modality tags for CORE/SC cases. Returns stats."""
    with get_conn() as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(cases)").fetchall()}
        if "modalities" not in cols:
            conn.execute("ALTER TABLE cases ADD COLUMN modalities TEXT")
        rows = conn.execute(
            """SELECT id FROM cases
               WHERE section IN ('core','sc') AND (? IS NULL OR section=?)""",
            (section, section),
        ).fetchall()
        tagged = 0
        untagged = 0
        for row in rows:
            case_id = row["id"]
            tags = classify_modalities(_case_text(conn, case_id))
            if tags:
                tagged += 1
            else:
                untagged += 1
            conn.execute(
                "UPDATE cases SET modalities=? WHERE id=?",
                (json.dumps(tags), case_id),
            )
        return {"total": len(rows), "tagged": tagged, "untagged": untagged}


def get_case_modalities(modalities_json: str | None) -> list[str]:
    if not modalities_json:
        return []
    try:
        return json.loads(modalities_json)
    except (TypeError, ValueError):
        return []
