"""
Vision-based image extraction for EDiR_CORE.pdf pages.

Sends rendered page PNGs to Claude, gets back bounding boxes of clinical images
(X-rays, CTs, MRIs, etc.), crops them, and updates the DB.
Runs once locally; crops are committed to git so Streamlit Cloud needs no API key.
"""

import base64
import json
import re
from pathlib import Path

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import fitz
except ImportError:
    fitz = None

from core.database import get_conn

PDF_PATH = Path(__file__).parent.parent / "data" / "pdfs" / "EDiR_CORE.pdf"
DOI_PAT  = re.compile(r'https://doi\.org/[^\s)]+')

CROPS_DIR   = Path(__file__).parent.parent / "data" / "crops"
IMAGES_DIR  = Path(__file__).parent.parent / "data" / "page_images"

VISION_PROMPT = """This is a page from the EDiR radiology exam textbook.

Find every radiological/clinical image: X-ray, CT, MRI, ultrasound, mammogram, nuclear medicine, angiogram, etc.

Do NOT include: text blocks, page numbers, headers, logos, captions, or non-medical diagrams.

For each clinical image return its bounding box as fractions of page size (0.0–1.0), the figure label if visible, the imaging modality, and which question it belongs to. Use "Q1", "Q2", etc. based on the nearest question marker above the image, or "vignette" if it appears before any question.

Also list any video DOI links visible on the page.

Reply with ONLY valid JSON — no markdown, no explanation:
{
  "images": [
    {
      "bbox": {"top": 0.05, "left": 0.08, "bottom": 0.58, "right": 0.92},
      "figure_label": "Fig. 1.1",
      "modality": "plain X-ray abdomen",
      "belongs_to": "vignette"
    }
  ],
  "video_links": []
}

If there are no clinical images on this page, return: {"images": [], "video_links": []}"""


def _call_claude(client, png_path: Path) -> dict:
    with open(png_path, "rb") as f:
        img_b64 = base64.standard_b64encode(f.read()).decode()

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": img_b64,
                }},
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
    )

    text = resp.content[0].text.strip()
    # Strip markdown code fences if present
    text = re.sub(r'^```(?:json)?\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"images": [], "video_links": []}


def _crop(png_path: Path, bbox: dict, out_path: Path) -> bool:
    if Image is None:
        return False
    try:
        img = Image.open(png_path)
        w, h = img.size
        l = int(max(0.0, bbox["left"])   * w)
        t = int(max(0.0, bbox["top"])    * h)
        r = int(min(1.0, bbox["right"])  * w)
        b = int(min(1.0, bbox["bottom"]) * h)
        if r <= l or b <= t:
            return False
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.crop((l, t, r, b)).save(out_path, optimize=True)
        return True
    except Exception:
        return False


def run_vision_enhancement(api_key: str, progress_callback=None) -> tuple[bool, str]:
    """
    For every question page in the DB, call Claude vision to extract clinical images,
    crop them, and update questions.page_images with the crop paths.
    Returns (success, message).
    """
    if anthropic is None:
        return False, "anthropic package not installed. Run: pip install anthropic"
    if Image is None:
        return False, "Pillow not installed. Run: pip install pillow"
    if not api_key:
        return False, "No ANTHROPIC_API_KEY provided."

    client = anthropic.Anthropic(api_key=api_key)

    with get_conn() as conn:
        chapters = conn.execute("SELECT * FROM chapters ORDER BY number").fetchall()

    total_pages_processed = 0

    for ch in chapters:
        cases = _get_cases_with_questions(ch["id"])
        if not cases:
            continue

        # Collect all question-page data for this chapter
        # page_idx → {q_number → [question_ids]}
        page_q_map: dict[int, dict[str, list[int]]] = {}
        for case in cases:
            for q in case["questions"]:
                imgs = json.loads(q["page_images"] or "[]")
                for img_path in imgs:
                    # Extract page index from path like data/page_images/page_002.png
                    m = re.search(r'page_(\d+)', img_path)
                    if not m:
                        continue
                    pidx = int(m.group(1))
                    page_q_map.setdefault(pidx, {})
                    key = f"Q{q['q_number']}"
                    page_q_map[pidx].setdefault(key, []).append(q["id"])
                    # Vignette images → attach to Q1
                    page_q_map[pidx].setdefault("vignette", []).extend(
                        [qid for qid in page_q_map[pidx].get("Q1", [])
                         if qid not in page_q_map[pidx].get("vignette", [])]
                    )

        for page_idx, q_map in sorted(page_q_map.items()):
            png_path = IMAGES_DIR / f"page_{page_idx:03d}.png"
            if not png_path.exists():
                continue

            if progress_callback:
                progress_callback(
                    f"Vision: Ch{ch['number']} — page {page_idx}…",
                    None
                )

            page_data   = _call_claude(client, png_path)
            images      = page_data.get("images", [])
            video_links = page_data.get("video_links", [])

            # Group crops by question
            q_crops: dict[int, list[str]] = {}

            for img_idx, img_info in enumerate(images):
                crop_rel  = f"data/crops/p{page_idx:03d}_img{img_idx:02d}.png"
                crop_path = Path(__file__).parent.parent / crop_rel

                if not _crop(png_path, img_info["bbox"], crop_path):
                    continue

                belongs = img_info.get("belongs_to", "vignette")
                target_ids = q_map.get(belongs) or q_map.get("vignette", [])
                for qid in target_ids:
                    q_crops.setdefault(qid, [])
                    if crop_rel not in q_crops[qid]:
                        q_crops[qid].append(crop_rel)

            # Update DB — crops and video links (links go to Q1 / vignette question)
            with get_conn() as conn:
                for qid, crops in q_crops.items():
                    if crops:
                        conn.execute(
                            "UPDATE questions SET page_images=? WHERE id=?",
                            (json.dumps(crops), qid)
                        )
                if video_links:
                    vignette_ids = q_map.get("vignette") or q_map.get("Q1", [])
                    for qid in vignette_ids:
                        existing = conn.execute(
                            "SELECT video_links FROM questions WHERE id=?", (qid,)
                        ).fetchone()
                        existing_links = json.loads(existing["video_links"] or "[]") if existing else []
                        merged = list(dict.fromkeys(existing_links + video_links))
                        conn.execute(
                            "UPDATE questions SET video_links=? WHERE id=?",
                            (json.dumps(merged), qid)
                        )

            total_pages_processed += 1

    return True, f"Vision enhancement complete — {total_pages_processed} pages processed."


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_cases_with_questions(chapter_id: int) -> list[dict]:
    with get_conn() as conn:
        cases = conn.execute(
            "SELECT * FROM cases WHERE chapter_id=? ORDER BY case_number",
            (chapter_id,)
        ).fetchall()
        result = []
        for case in cases:
            qs = conn.execute(
                "SELECT id, q_number, page_images FROM questions WHERE case_id=? ORDER BY q_number",
                (case["id"],)
            ).fetchall()
            result.append({"case": dict(case), "questions": [dict(q) for q in qs]})
        return result


def run_doi_extraction() -> tuple[bool, str]:
    """
    Read DOI video links directly from the PDF text (no API call needed).
    Associates each doi.org link with the question whose page it appears on,
    then updates questions.video_links in the DB.
    """
    if fitz is None:
        return False, "PyMuPDF not installed."
    if not PDF_PATH.exists():
        return False, f"PDF not found: {PDF_PATH}"

    doc = fitz.open(str(PDF_PATH))
    updated = 0

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, q_number, page_images FROM questions"
        ).fetchall()

        for row in rows:
            page_imgs = json.loads(row["page_images"] or "[]")
            # collect DOI links from all pages this question references
            doi_links: list[str] = []
            for img_path in page_imgs:
                m = re.search(r'page_(\d+)', img_path)
                if not m:
                    continue
                page_idx = int(m.group(1))
                if page_idx >= len(doc):
                    continue
                text = doc[page_idx].get_text("text")
                for link in DOI_PAT.findall(text):
                    if link not in doi_links:
                        doi_links.append(link)

            if doi_links:
                conn.execute(
                    "UPDATE questions SET video_links=? WHERE id=?",
                    (json.dumps(doi_links), row["id"])
                )
                updated += 1

    return True, f"DOI extraction complete — {updated} questions updated."
