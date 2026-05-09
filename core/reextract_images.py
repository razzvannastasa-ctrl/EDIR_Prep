"""
Targeted image re-extraction.

Re-runs ONLY the image-location step for each section group (no text/answer
re-extraction). Fixes wrong crop assignments caused by the loop bug in the
original import without touching any question text or answers.

Cost: same page images sent as a full import, but shorter prompts and
      smaller responses (~similar total, but all text data is preserved).
"""

import json
import re
import time
from collections import defaultdict
from pathlib import Path

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import fitz
except ImportError:
    fitz = None

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

from core.vision_import import (
    _extract_toc, _build_groups,
    _render, _img_msg, _parse_json, _crop_and_save,
    CROPS_DIR,
)
from core.database import get_conn

# ── Prompts ───────────────────────────────────────────────────────────────────

_PROMPT_CASES = """\
These pages are from a radiology textbook.
The first {nq} image(s) are QUESTION pages. The last {na} image(s) are ANSWER pages.
This section contains {n_cases} case(s).

Find every clinical image (X-ray, CT, MRI, ultrasound, histology).
Do NOT include text blocks, logos, tables, or diagrams.

For each clinical image return:
- case_number : which case it belongs to (1, 2, 3 …)
- question_number : question within that case (1, 2 …), or 0 for a vignette/intro image before Q1
- page_offset : 0-based index into ALL pages sent (question pages first, then answer pages)
- bbox : bounding box as fractions of page size (top, left, bottom, right)

Return ONLY valid JSON — no commentary:
{{"images": [{{"case_number": 1, "question_number": 1, "page_offset": 0, "bbox": {{"top": 0.05, "left": 0.05, "bottom": 0.55, "right": 0.95}}}}]}}
If no clinical images are present return {{"images": []}}
"""

_PROMPT_MRQ = """\
These pages are from a radiology textbook (MRQ section).
The first {nq} image(s) are QUESTION pages. The last {na} image(s) are ANSWER pages.

Find every clinical image (X-ray, CT, MRI, ultrasound, histology).
Do NOT include text blocks, logos, tables, or diagrams.

For each clinical image return:
- question_number : which MRQ question it belongs to (1, 2, 3 …)
- page_offset : 0-based index into ALL pages sent (question pages first, then answer pages)
- bbox : bounding box as fractions of page size (top, left, bottom, right)

Return ONLY valid JSON — no commentary:
{{"images": [{{"question_number": 1, "page_offset": 0, "bbox": {{"top": 0.05, "left": 0.05, "bottom": 0.55, "right": 0.95}}}}]}}
If no clinical images are present return {{"images": []}}
"""


# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_group_cases(chapter_num: int, section: str) -> list[dict]:
    """Return [{case_id, q_id_map: {q_number: q_id}}] ordered by case_number."""
    with get_conn() as conn:
        cases = conn.execute(
            """SELECT c.id FROM cases c
               JOIN chapters ch ON c.chapter_id = ch.id
               WHERE ch.number=? AND c.section=?
               ORDER BY c.case_number""",
            (chapter_num, section),
        ).fetchall()
        result = []
        for case in cases:
            qs = conn.execute(
                "SELECT id, q_number FROM questions WHERE case_id=? ORDER BY q_number",
                (case["id"],),
            ).fetchall()
            result.append({"case_id": case["id"],
                            "q_id_map": {q["q_number"]: q["id"] for q in qs}})
        return result


def _write_crops(q_id_crops: dict):
    with get_conn() as conn:
        for q_id, crops in q_id_crops.items():
            if crops:
                conn.execute(
                    "UPDATE questions SET page_images=? WHERE id=?",
                    (json.dumps(crops), q_id),
                )


# ── Core processing ───────────────────────────────────────────────────────────

def _assign_images(raw_images: list, all_pages: list,
                   case_q_maps: list[dict], section: str, n_q_pages: int) -> dict:
    """
    Crop images and build {q_id: [crop_paths]} for the whole group at once.
    Uses a single global counter so filenames never collide across cases.
    Only uses images from question pages (p_off < n_q_pages).
    """
    from pathlib import Path as _Path

    img_counter: dict[int, int] = defaultdict(int)
    q_crops: dict[int, list] = defaultdict(list)

    for img_info in raw_images:
        if section == "mrq":
            case_idx = 0
            q_num    = img_info.get("question_number", 1)
        else:
            case_idx = img_info.get("case_number", 1) - 1
            q_num    = img_info.get("question_number", 1)

        p_off = img_info.get("page_offset", 0)
        bbox  = img_info.get("bbox", {})

        if not (0 <= p_off < len(all_pages)):
            continue
        if p_off >= n_q_pages:
            continue  # skip images from answer pages
        if not (0 <= case_idx < len(case_q_maps)):
            continue

        pdf_page = all_pages[p_off]
        idx      = img_counter[pdf_page]
        img_counter[pdf_page] += 1

        crop_rel  = f"data/crops/p{pdf_page:03d}_img{idx:02d}.png"
        crop_path = _Path(__file__).parent.parent / crop_rel

        if not _crop_and_save(_DOC, pdf_page, bbox, crop_path):
            continue

        q_id_map = case_q_maps[case_idx]
        q_id     = q_id_map.get(q_num)
        if q_id is None and q_num == 0:
            q_id = q_id_map.get(min(q_id_map)) if q_id_map else None
        if q_id is not None:
            q_crops[q_id].append(crop_rel)

    return dict(q_crops)


# module-level doc handle so _assign_images can access it without passing it
_DOC = None


# ── Entry point ───────────────────────────────────────────────────────────────

def run_image_reextraction(pdf_path, api_key, progress_callback=None):
    global _DOC

    if anthropic is None:
        return False, "anthropic package not installed."
    if fitz is None:
        return False, "PyMuPDF not installed."
    if PILImage is None:
        return False, "Pillow not installed."
    if not api_key:
        return False, "No API key provided."

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return False, f"PDF not found: {pdf_path}"

    client = anthropic.Anthropic(api_key=api_key)
    _DOC   = fitz.open(str(pdf_path))

    if progress_callback:
        progress_callback("Reading table of contents from bookmarks…", 0.0)

    toc = _extract_toc(client, _DOC)
    if not toc:
        _DOC.close()
        return False, "Could not read TOC. Make sure the PDF has bookmarks."

    groups = _build_groups(toc)

    # Clear old crops
    CROPS_DIR.mkdir(parents=True, exist_ok=True)
    for f in CROPS_DIR.glob("*.png"):
        f.unlink()

    # Reset all page_images in DB
    with get_conn() as conn:
        conn.execute("UPDATE questions SET page_images='[]'")

    total          = len(groups)
    n_imgs_total   = 0

    for gi, group in enumerate(groups):
        ch      = group["chapter"]
        sec     = group["section"]
        q_pages = group["q_pages"]
        a_pages = group["a_pages"]
        all_pages = q_pages + a_pages

        if not all_pages:
            continue

        db_cases = _get_group_cases(ch, sec)
        if not db_cases:
            continue

        if progress_callback:
            progress_callback(
                f"Ch{ch} {sec.upper()} — {len(db_cases)} case(s), "
                f"{len(q_pages)}Q + {len(a_pages)}A pages…",
                gi / total,
            )

        nq, na = len(q_pages), len(a_pages)
        page_imgs = [_img_msg(_render(_DOC, p, zoom=2.0)) for p in all_pages]

        if sec == "mrq":
            prompt = _PROMPT_MRQ.format(nq=nq, na=na)
        else:
            prompt = _PROMPT_CASES.format(nq=nq, na=na, n_cases=len(db_cases))

        data = None
        for attempt in range(2):
            try:
                resp = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=2048,
                    messages=[{"role": "user",
                               "content": page_imgs + [{"type": "text", "text": prompt}]}],
                )
                data = _parse_json(resp.content[0].text)
                if data:
                    break
            except Exception:
                time.sleep(2 * (attempt + 1))

        if not data:
            continue

        raw_images = data.get("images", [])
        if not raw_images:
            continue

        case_q_maps   = [c["q_id_map"] for c in db_cases]
        q_id_crops    = _assign_images(raw_images, all_pages, case_q_maps, sec, nq)
        _write_crops(q_id_crops)
        n_imgs_total += sum(len(v) for v in q_id_crops.values())

        time.sleep(0.1)

    _DOC.close()
    _DOC = None

    if progress_callback:
        progress_callback("Done.", 1.0)

    return True, f"Image re-extraction complete — {n_imgs_total} image crop(s) assigned."


# ── Free cleanup (no Vision API) ──────────────────────────────────────────────

def cleanup_answer_images(pdf_path, progress_callback=None) -> tuple[bool, str]:
    """
    Remove crops sourced from answer pages from questions.page_images.
    Reads page ranges from PDF bookmarks — no Vision API calls, no cost.
    """
    if fitz is None:
        return False, "PyMuPDF not installed."

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return False, f"PDF not found: {pdf_path}"

    from core.vision_import import _toc_from_bookmarks, _build_groups

    if progress_callback:
        progress_callback("Reading TOC from bookmarks…", 0.0)

    doc    = fitz.open(str(pdf_path))
    toc    = _toc_from_bookmarks(doc)
    doc.close()

    if not toc:
        return False, "No bookmarks found in PDF."

    groups = _build_groups(toc)

    # All PDF page indices that are answer pages across all groups
    answer_pages: set[int] = set()
    for g in groups:
        answer_pages.update(g["a_pages"])

    # Crop filenames encode the page index: p{page:03d}_img{idx:02d}.png
    page_re = re.compile(r'[/\\]p(\d{3})_img\d{2}\.png$')

    n_removed = 0
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, page_images FROM questions WHERE page_images IS NOT NULL AND page_images != '[]'"
        ).fetchall()

        for i, row in enumerate(rows):
            if progress_callback and i % 50 == 0:
                progress_callback(f"Checking question {i}/{len(rows)}…", i / max(len(rows), 1))
            try:
                paths = json.loads(row["page_images"])
            except Exception:
                continue

            cleaned = []
            for p in paths:
                m = page_re.search(p)
                if m and int(m.group(1)) in answer_pages:
                    n_removed += 1
                else:
                    cleaned.append(p)

            if len(cleaned) != len(paths):
                conn.execute(
                    "UPDATE questions SET page_images=? WHERE id=?",
                    (json.dumps(cleaned), row["id"]),
                )

    return True, f"Removed {n_removed} answer-page image(s) from question records."
