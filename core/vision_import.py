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


# ── Pass 1: TOC extraction from PDF bookmarks ─────────────────────────────────

def _extract_toc(client, doc) -> dict | None:
    """
    Read the book structure from the PDF's built-in bookmarks (outline).
    Falls back to Vision if the PDF has no bookmarks.
    Returns: {arabic_start_pdf_index, chapters: [{number, title, sections}]}
    """
    result = _toc_from_bookmarks(doc)
    if result:
        return result
    return _extract_toc_vision(client, doc)


def _toc_from_bookmarks(doc) -> dict | None:
    raw = doc.get_toc()   # [(level, title, fitz_page_1based), ...]
    if not raw:
        return None

    ch_pat = re.compile(r'^(\d+)\s*[:\-]?\s*')

    # Collect chapter-level entries (level 1 with a leading number)
    chapters_raw = []
    for raw_idx, (lv, title, page) in enumerate(raw):
        m = ch_pat.match(title.strip()) if lv == 1 else None
        if m:
            num = int(m.group(1))
            ch_title = title.strip()[m.end():].strip().lstrip(':').strip() or f"Chapter {num}"
            chapters_raw.append((raw_idx, num, ch_title, page))

    if not chapters_raw:
        return None

    # arabic_start_pdf_index: 0-based PDF index of printed Arabic page 1
    # = fitz page of chapter 1 - 1  (chapter 1 always starts at Arabic page 1)
    arabic_start = chapters_raw[0][3] - 1

    def to_arabic(fitz_p: int) -> int:
        return fitz_p - arabic_start   # fitz is 1-based so this gives arabic page number

    def parse_sections(sub: list[tuple], ch_end_fitz: int) -> list[dict]:
        mrq_q = sc_q = core_q = None
        mrq_a = sc_a = core_a = None
        bib_p = ch_end_fitz
        in_answers = False

        for lv, title, page in sub:
            tl = title.lower()
            if 'bibliograph' in tl:
                bib_p = min(bib_p, page)
                continue
            if lv == 2 and 'answer' in tl:
                in_answers = True
                continue
            if not in_answers:
                if re.search(r'multiple.?response|mrq', tl) and mrq_q is None:
                    mrq_q = page
                elif re.search(r'short.?case', tl) and sc_q is None:
                    sc_q = page
                elif re.search(r'\bcore\b', tl) and core_q is None:
                    core_q = page
            else:
                if re.search(r'multiple.?response|mrq', tl) and mrq_a is None:
                    mrq_a = page
                elif re.search(r'short.?case', tl) and sc_a is None:
                    sc_a = page
                elif re.search(r'\bcore\b|reasoning', tl) and core_a is None:
                    core_a = page

        q_bounds = sorted(p for p in [mrq_q, sc_q, core_q] if p is not None)
        a_bounds = sorted(p for p in [mrq_a, sc_a, core_a] if p is not None)
        # questions end before answers block; answers end before bibliography
        q_bounds.append(min(a_bounds) if a_bounds else bib_p)
        a_bounds.append(bib_p)

        def end_of(start_p, bounds):
            for b in bounds:
                if b > start_p:
                    return b - 1
            return start_p

        sections = []
        if mrq_q and mrq_a:
            sections.append({"type": "mrq",
                              "q_start": to_arabic(mrq_q), "q_end": to_arabic(end_of(mrq_q, q_bounds)),
                              "a_start": to_arabic(mrq_a), "a_end": to_arabic(end_of(mrq_a, a_bounds))})
        if sc_q and sc_a:
            sections.append({"type": "sc",
                              "q_start": to_arabic(sc_q),  "q_end": to_arabic(end_of(sc_q, q_bounds)),
                              "a_start": to_arabic(sc_a),  "a_end": to_arabic(end_of(sc_a, a_bounds))})
        if core_q and core_a:
            sections.append({"type": "core",
                              "q_start": to_arabic(core_q), "q_end": to_arabic(end_of(core_q, q_bounds)),
                              "a_start": to_arabic(core_a), "a_end": to_arabic(end_of(core_a, a_bounds))})
        return sections

    result_chapters = []
    for ci, (raw_idx, num, title, page) in enumerate(chapters_raw):
        next_raw_idx  = chapters_raw[ci + 1][0] if ci + 1 < len(chapters_raw) else len(raw)
        ch_end_fitz   = chapters_raw[ci + 1][3] if ci + 1 < len(chapters_raw) else len(doc) + 1
        sub = [(lv, t, p) for lv, t, p in
               [(r[0], r[1], r[2]) for r in raw[raw_idx + 1: next_raw_idx]]]
        secs = parse_sections(sub, ch_end_fitz)
        result_chapters.append({"number": num, "title": title, "sections": secs})

    return {"arabic_start_pdf_index": arabic_start, "chapters": result_chapters}


def _extract_toc_vision(client, doc) -> dict | None:
    """Vision fallback: send only the TOC pages (10-15) at low zoom."""
    _PROMPT = """\
These pages are the Table of Contents of the EDiR radiology textbook.
The main content uses Arabic page numbers starting at 1.
Each chapter has up to three section types: "core", "mrq", "sc".
Extract the complete structure and return ONLY valid JSON:
{"arabic_start_pdf_index": 17,
 "chapters": [{"number": 1, "title": "...", "sections": [
   {"type": "mrq", "q_start": 2, "q_end": 7, "a_start": 24, "a_end": 27},
   {"type": "sc",  "q_start": 8, "q_end": 19, "a_start": 28, "a_end": 30},
   {"type": "core","q_start": 20,"q_end": 23, "a_start": 31, "a_end": 32}
 ]}]}
arabic_start_pdf_index is the 0-based PDF page index where Arabic page 1 appears."""

    images = [_img_msg(_render(doc, i, zoom=1.0)) for i in range(10, min(16, len(doc)))]
    content = images + [{"type": "text", "text": _PROMPT}]
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=4096,
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
      "video_links": [],
      "page_offset": 0
    }}
  ]
}}

Rules:
- Copy text VERBATIM — do not paraphrase or correct
- correct_options: the letter(s) of correct answers, e.g. ["a"] or ["b","d"]
- video_links: any doi.org URLs visible anywhere on the pages
- explanation: text that follows the answer key on the answer page
- page_offset: 0-based index into the question images sent (which page this question appears on)
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

        p_off     = q.get("page_offset", 0)
        page_imgs = []
        if 0 <= p_off < len(group["q_pages"]):
            page_imgs = [_save_page(doc, group["q_pages"][p_off])]
        elif group["q_pages"]:
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
        return False, (
            "Could not extract the table of contents. "
            "Make sure the PDF has bookmarks/outline entries."
        )

    if progress_callback:
        n_ch = len(toc.get("chapters", []))
        progress_callback(
            f"TOC: {n_ch} chapters found (content starts at PDF page {toc['arabic_start_pdf_index']})",
            0.1
        )

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
