"""
Vision-based PDF import pipeline.

Pass 1 — TOC    : send the first ~20 pages to Claude to extract the full
                  book structure (chapter titles, section page ranges) from
                  the Table of Contents. Converts printed Arabic page numbers
                  to 0-based PDF indices using the front-matter offset.
Pass 2 — Extract: send each section's question+answer pages together to
                  Claude and get back fully-structured case/question data.
"""

import base64
import json
import re
import time
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

from core.database import get_conn, init_db

IMAGES_DIR = Path(__file__).parent.parent / "data" / "page_images"
CROPS_DIR  = Path(__file__).parent.parent / "data" / "crops"


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _render(doc, page_idx: int, zoom: float) -> bytes:
    mat = fitz.Matrix(zoom, zoom)
    return doc[page_idx].get_pixmap(matrix=mat).tobytes("png")


def _b64(png: bytes) -> str:
    return base64.standard_b64encode(png).decode()


def _img_msg(png: bytes) -> dict:
    return {
        "type": "image",
        "source": {"type": "base64", "media_type": "image/png", "data": _b64(png)},
    }


def _parse_json(text: str) -> dict | list | None:
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _letters_to_indices(val) -> list[int]:
    """Convert answer keys like ['a','c'] or [0,2] to 0-indexed ints."""
    result = []
    for v in (val or []):
        if isinstance(v, int):
            result.append(v)
        elif isinstance(v, str):
            s = v.strip().lower()
            if s in "abcde":
                result.append(ord(s) - ord("a"))
            elif s.isdigit():
                result.append(int(s))
    return result


# ── Pass 1: TOC extraction ────────────────────────────────────────────────────

_TOC_PROMPT = """\
These are the first pages of the EDiR (Essential Guide in Radiology) textbook.

The book has two page-numbering systems:
- Front matter uses Roman numerals (I, II, … XV). The Table of Contents is in this section.
- Main content uses Arabic numerals starting at 1.

Your tasks:
1. Find the Table of Contents and extract the complete book structure.
2. Identify which 0-based image index (counting from the first image in this batch) \
corresponds to the first Arabic page "1" of the main content.

Each chapter contains up to three section types:
- "core"  CORE Cases (Clinical Oriented Reasoning Evaluation)
- "mrq"   Multiple Response Questions
- "sc"    Short Cases

The TOC lists printed Arabic page numbers. Extract the start and end printed page \
number for the question pages and the answer pages of each section.
If the TOC only shows a start page (no explicit end), infer the end from where the \
next section starts (i.e. end = next_start - 1).

Return ONLY valid JSON — no markdown, no explanation:
{
  "arabic_start_pdf_index": 16,
  "chapters": [
    {
      "number": 1,
      "title": "Chapter title exactly as written",
      "sections": [
        {
          "type": "core",
          "q_start": 1,
          "q_end": 14,
          "a_start": 201,
          "a_end": 214
        },
        {
          "type": "mrq",
          "q_start": 15,
          "q_end": 24,
          "a_start": 215,
          "a_end": 222
        },
        {
          "type": "sc",
          "q_start": 25,
          "q_end": 36,
          "a_start": 223,
          "a_end": 232
        }
      ]
    }
  ]
}

Omit section types not present in a chapter.
"""


def _extract_toc(client, doc) -> dict | None:
    n = min(20, len(doc))
    images = [_img_msg(_render(doc, i, zoom=1.5)) for i in range(n)]
    content = images + [{"type": "text", "text": _TOC_PROMPT}]

    for attempt in range(3):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                messages=[{"role": "user", "content": content}],
            )
            data = _parse_json(resp.content[0].text)
            if data and "chapters" in data and "arabic_start_pdf_index" in data:
                return data
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


# ── Build extraction groups from TOC ─────────────────────────────────────────

def _build_groups(toc: dict) -> list[dict]:
    """
    Convert TOC structure into extraction groups with exact PDF page indices.
    arabic_start_pdf_index: 0-based PDF index of printed Arabic page 1.
    pdf_index = arabic_page_number - 1 + arabic_start_pdf_index
    """
    offset = toc.get("arabic_start_pdf_index", 0)

    def to_pdf(arabic: int) -> int:
        return arabic - 1 + offset

    def page_range(start: int, end: int) -> list[int]:
        return list(range(to_pdf(start), to_pdf(end) + 1))

    groups = []
    for ch in toc.get("chapters", []):
        for sec in ch.get("sections", []):
            if sec.get("type") not in ("core", "mrq", "sc"):
                continue
            groups.append({
                "chapter":       ch["number"],
                "chapter_title": ch["title"],
                "section":       sec["type"],
                "q_pages":       page_range(sec["q_start"], sec["q_end"]),
                "a_pages":       page_range(sec["a_start"], sec["a_end"]),
            })
    return groups


# ── Pass 2 prompts ────────────────────────────────────────────────────────────

_MRQ_PROMPT = """\
Chapter {ch}: "{title}" — Multiple Response Questions (MRQs)

The first {nq} image(s) are QUESTION pages. The last {na} image(s) are ANSWER pages.

Extract every MRQ with its correct answer(s). Return ONLY valid JSON:
{{
  "questions": [
    {{
      "number": 1,
      "text": "exact question text as written",
      "options": ["a. option text", "b. option text", "c. option text", "d. option text", "e. option text"],
      "correct_options": ["a", "c"],
      "explanation": "explanation text, or empty string if none",
      "video_links": []
    }}
  ]
}}

Rules:
- Copy text VERBATIM — do not paraphrase or correct
- correct_options: the letter(s) of correct answers, e.g. ["a"] or ["b","d"]
- video_links: any doi.org URLs visible anywhere on the pages
- explanation: text that follows the answer key on the answer page
"""

_CORE_PROMPT = """\
Chapter {ch}: "{title}" — CORE Cases (Clinical Oriented Reasoning Evaluation)

The first {nq} image(s) are QUESTION pages. The last {na} image(s) are ANSWER pages.

CORE format: clinical vignette → numbered questions Q1, Q2 … → numbered answers A1, A2 …
There may be more than one CORE case across these pages.

Return ONLY valid JSON:
{{
  "cases": [
    {{
      "vignette": "clinical presentation text",
      "questions": [
        {{
          "number": 1,
          "text": "exact question text",
          "type": "free_text",
          "options": [],
          "answer": "exact answer text",
          "explanation": "explanation if present, else empty string",
          "video_links": [],
          "page_offset": 0
        }}
      ]
    }}
  ]
}}

Rules:
- Copy text VERBATIM
- type: "free_text" | "single_choice" | "multiple_choice"
- options: list of strings for choice questions, empty list for free_text
- Match each Q-number to its A-number exactly
- page_offset: 0-based index into the images sent (which page this question appears on)
- video_links: any doi.org URLs visible on the pages
"""

_SC_PROMPT = """\
Chapter {ch}: "{title}" — Short Cases

The first {nq} image(s) are QUESTION pages. The last {na} image(s) are ANSWER pages.

Short Cases: brief clinical history + clinical image + 2–4 questions, followed by answers.
Multiple short cases may appear across these pages.

Return ONLY valid JSON:
{{
  "cases": [
    {{
      "vignette": "brief clinical history / presentation",
      "questions": [
        {{
          "number": 1,
          "text": "exact question text",
          "type": "free_text",
          "options": [],
          "answer": "exact answer text",
          "explanation": "",
          "video_links": [],
          "page_offset": 0
        }}
      ]
    }}
  ]
}}

Rules:
- Copy text VERBATIM
- Each short case is a separate entry in "cases"
- page_offset: 0-based index into the images sent (which page this question appears on)
"""


# ── Pass 2: Extraction ────────────────────────────────────────────────────────

def _extract_group(client, doc, group: dict, zoom: float = 2.0) -> dict | None:
    ch    = group["chapter"]
    sec   = group["section"]
    title = group["chapter_title"]
    q_pages = group["q_pages"]
    a_pages = group["a_pages"]

    all_pages = q_pages + a_pages
    if not all_pages:
        return None

    nq, na = len(q_pages), len(a_pages)
    images = [_img_msg(_render(doc, p, zoom)) for p in all_pages]

    if sec == "mrq":
        prompt = _MRQ_PROMPT.format(ch=ch, title=title, nq=nq, na=na)
        max_tok = 4096
    elif sec == "core":
        prompt = _CORE_PROMPT.format(ch=ch, title=title, nq=nq, na=na)
        max_tok = 4096
    elif sec == "sc":
        prompt = _SC_PROMPT.format(ch=ch, title=title, nq=nq, na=na)
        max_tok = 8192
    else:
        return None

    content = images + [{"type": "text", "text": prompt}]

    for attempt in range(2):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tok,
                messages=[{"role": "user", "content": content}],
            )
            data = _parse_json(resp.content[0].text)
            if data:
                return data
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


# ── Image cropping ────────────────────────────────────────────────────────────

def _crop_and_save(doc, page_idx: int, bbox: dict,
                   crop_path: Path, zoom: float = 2.0) -> bool:
    if PILImage is None:
        return False
    try:
        png = _render(doc, page_idx, zoom)
        img = PILImage.open(__import__("io").BytesIO(png))
        w, h = img.size
        l = int(max(0.0, bbox.get("left",   0)) * w)
        t = int(max(0.0, bbox.get("top",    0)) * h)
        r = int(min(1.0, bbox.get("right",  1)) * w)
        b = int(min(1.0, bbox.get("bottom", 1)) * h)
        if r <= l or b <= t:
            return False
        crop_path.parent.mkdir(parents=True, exist_ok=True)
        img.crop((l, t, r, b)).save(crop_path, optimize=True)
        return True
    except Exception:
        return False


# ── DB insert helpers ─────────────────────────────────────────────────────────

def _save_page(doc, page_idx: int, zoom: float = 2.0) -> str:
    """Render and save a page to disk; return relative path."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    out = IMAGES_DIR / f"page_{page_idx:03d}.png"
    if not out.exists():
        png = _render(doc, page_idx, zoom)
        out.write_bytes(png)
    return f"data/page_images/page_{page_idx:03d}.png"


def _insert_mrq_group(data: dict, chapter_id: int, doc, group: dict):
    from core.database import insert_case, insert_question, insert_answer
    questions = data.get("questions", [])
    if not questions:
        return

    case_id = insert_case(chapter_id, 1, None, section="mrq")

    for q in questions:
        q_num   = int(q.get("number", 0))
        q_text  = q.get("text", "").strip()
        options = q.get("options", [])
        correct = _letters_to_indices(q.get("correct_options", []))
        exp     = q.get("explanation", "").strip()
        links   = q.get("video_links", [])

        q_type = "single_choice" if len(correct) == 1 else "multiple_choice"

        # page_images: first question page as reference
        page_imgs = []
        if group["q_pages"]:
            page_imgs = [_save_page(doc, group["q_pages"][0])]

        q_id = insert_question(case_id, q_num, q_text, q_type,
                               options or None, page_imgs)
        insert_answer(q_id, "", correct or None, exp, [])

        if links:
            with get_conn() as conn:
                conn.execute("UPDATE questions SET video_links=? WHERE id=?",
                             (json.dumps(links), q_id))


def _insert_case_group(data: dict, chapter_id: int, section: str,
                       doc, group: dict):
    from core.database import insert_case, insert_question, insert_answer
    cases = data.get("cases", [])
    all_pages = group["q_pages"] + group["a_pages"]

    for case_num, case in enumerate(cases, 1):
        vignette = (case.get("vignette") or "").strip()
        case_id  = insert_case(chapter_id, case_num, vignette or None, section=section)

        for q in case.get("questions", []):
            q_num   = int(q.get("number", 0))
            q_text  = q.get("text", "").strip()
            q_type  = q.get("type", "free_text")
            options = q.get("options", [])
            answer  = q.get("answer", "").strip()
            exp     = q.get("explanation", "").strip()
            links   = q.get("video_links", [])
            p_off   = q.get("page_offset", 0)

            # Map page_offset to the actual PDF page index
            page_imgs = []
            if 0 <= p_off < len(all_pages):
                page_imgs = [_save_page(doc, all_pages[p_off])]
            elif group["q_pages"]:
                page_imgs = [_save_page(doc, group["q_pages"][0])]

            q_id = insert_question(case_id, q_num, q_text, q_type,
                                   options or None, page_imgs)
            insert_answer(q_id, answer, None, exp, [])

            if links:
                with get_conn() as conn:
                    conn.execute("UPDATE questions SET video_links=? WHERE id=?",
                                 (json.dumps(links), q_id))


# ── Main entry point ──────────────────────────────────────────────────────────

def run_vision_import(pdf_path: str | Path, api_key: str,
                      progress_callback=None) -> tuple[bool, str]:
    """
    Full Vision-based import pipeline.
    Wipes existing DB, processes all pages from pdf_path, inserts content.
    Returns (success, message).
    """
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

    from core.database import clear_all, insert_chapter

    client = anthropic.Anthropic(api_key=api_key)
    doc    = fitz.open(str(pdf_path))
    n      = len(doc)

    init_db()
    clear_all()

    # Clear old crops and page images
    for d in (CROPS_DIR, IMAGES_DIR):
        if d.exists():
            for f in d.glob("*.png"):
                f.unlink()

    # ── Pass 1: Extract TOC ───────────────────────────────────────────────────
    if progress_callback:
        progress_callback("Pass 1: Reading table of contents…", 0.0)

    toc = _extract_toc(client, doc)
    if not toc:
        doc.close()
        return False, "Could not extract table of contents from the first 20 pages."

    if progress_callback:
        n_ch = len(toc.get("chapters", []))
        progress_callback(f"TOC found: {n_ch} chapter(s), offset={toc['arabic_start_pdf_index']}", 0.1)

    # Insert chapters into DB
    chapter_ids: dict[int, int] = {}
    for ch in toc.get("chapters", []):
        chapter_ids[ch["number"]] = insert_chapter(ch["number"], ch["title"])

    # Build extraction groups from TOC page ranges
    groups = _build_groups(toc)

    if progress_callback:
        progress_callback(f"Pass 2: Extracting {len(groups)} section(s)…", 0.15)

    for gi, group in enumerate(groups):
        ch  = group["chapter"]
        sec = group["section"]
        q_n = len(group["q_pages"])
        a_n = len(group["a_pages"])

        if progress_callback:
            progress_callback(
                f"Pass 2: Ch{ch} {sec.upper()} ({q_n}Q + {a_n}A pages)…",
                0.15 + gi / max(len(groups), 1) * 0.80,
            )

        data  = _extract_group(client, doc, group)
        ch_id = chapter_ids.get(ch)

        if not data or ch_id is None:
            continue

        if sec == "mrq":
            _insert_mrq_group(data, ch_id, doc, group)
        elif sec in ("core", "sc"):
            _insert_case_group(data, ch_id, sec, doc, group)

        time.sleep(0.1)

    doc.close()

    if progress_callback:
        progress_callback("Done.", 1.0)

    with get_conn() as conn:
        n_cases = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        n_qs    = conn.execute("SELECT COUNT(*) FROM questions").fetchone()[0]

    return True, f"Import complete — {n_cases} cases, {n_qs} questions across all sections."
