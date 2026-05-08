"""
Vision-based PDF import pipeline.

Pass 1 — Label  : classify every page (chapter, section type, role)
Pass 2 — Extract: send grouped pages (questions + answers) to Claude
                  and get back fully-structured case/question data.

The two-pass design means Claude never has to correlate questions with
answers across distant pages in a single call — we group them first,
then send them together.
"""

import base64
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


# ── Pass 1: Page labeling ─────────────────────────────────────────────────────

_LABEL_PROMPT = """\
This is page {idx} of the EDiR (Essential Guide in Radiology) book.

Classify this page. Return ONLY valid JSON — no markdown, no explanation:
{{
  "chapter": 1,
  "section": "mrq",
  "role": "questions",
  "title": ""
}}

Field rules:
- "chapter" : visible chapter number (integer), or null
- "section" : exactly one of:
    "mrq"    Multiple Response Questions (multiple-choice exam questions, labelled a–e)
    "sc"     Short Cases (brief clinical case + image + 2-4 questions)
    "core"   CORE Cases (Clinical Oriented Reasoning Evaluation — vignette + Q1/Q2…)
    "header" Chapter introduction / title page
    "bib"    Bibliography or references
    "other"  Preface, index, blank, etc.
- "role"    : "questions" | "answers" | "other"
- "title"   : chapter title string if this is a header page, else empty string
"""


def _label_page(client, png: bytes, page_idx: int) -> dict:
    prompt = _LABEL_PROMPT.format(idx=page_idx)
    for _ in range(2):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=150,
                messages=[{"role": "user", "content": [
                    _img_msg(png),
                    {"type": "text", "text": prompt},
                ]}],
            )
            data = _parse_json(resp.content[0].text)
            if data and "section" in data:
                return data
        except Exception:
            time.sleep(1)
    return {"chapter": None, "section": "other", "role": "other", "title": ""}


# ── Grouping ──────────────────────────────────────────────────────────────────

def _propagate_chapters(labels: dict[int, dict]) -> dict[int, dict]:
    """Fill null chapters by copying from the nearest preceding labeled page."""
    last_ch = None
    for idx in sorted(labels):
        ch = labels[idx].get("chapter")
        if ch is not None:
            last_ch = ch
        elif last_ch is not None and labels[idx].get("section") not in ("other", None):
            labels[idx] = {**labels[idx], "chapter": last_ch}
    return labels


def _group_labels(labels: dict[int, dict]) -> list[dict]:
    """
    Pair question pages with answer pages for the same (chapter, section).
    Returns list of groups: {chapter, section, q_pages, a_pages, chapter_title}
    """
    buckets: dict[tuple, dict] = defaultdict(lambda: {"q": [], "a": []})
    titles: dict[int, str] = {}

    for idx in sorted(labels):
        lbl  = labels[idx]
        ch   = lbl.get("chapter")
        sec  = lbl.get("section", "other")
        role = lbl.get("role", "other")

        if sec == "header" and ch and lbl.get("title"):
            titles[ch] = lbl["title"]

        if sec in ("mrq", "sc", "core") and ch is not None:
            key = (ch, sec)
            if role == "questions":
                buckets[key]["q"].append(idx)
            elif role == "answers":
                buckets[key]["a"].append(idx)

    groups = []
    for (ch, sec) in sorted(buckets):
        groups.append({
            "chapter":       ch,
            "section":       sec,
            "q_pages":       sorted(buckets[(ch, sec)]["q"]),
            "a_pages":       sorted(buckets[(ch, sec)]["a"]),
            "chapter_title": titles.get(ch, f"Chapter {ch}"),
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

    # ── Pass 1: Label every page ──────────────────────────────────────────────
    if progress_callback:
        progress_callback("Pass 1: Classifying pages…", 0.0)

    labels: dict[int, dict] = {}
    for i in range(n):
        png = _render(doc, i, zoom=1.0)   # small render — just need to read headers
        labels[i] = _label_page(client, png, i)
        if progress_callback:
            progress_callback(f"Pass 1: page {i+1}/{n}…", i / n * 0.35)
        time.sleep(0.05)

    labels = _propagate_chapters(labels)

    # Collect chapter titles and insert chapters
    chapter_titles: dict[int, str] = {}
    for lbl in labels.values():
        ch = lbl.get("chapter")
        t  = lbl.get("title", "")
        if ch and t and ch not in chapter_titles:
            chapter_titles[ch] = t

    chapter_ids: dict[int, int] = {}
    all_chs = sorted({lbl["chapter"] for lbl in labels.values()
                      if lbl.get("chapter") is not None})
    for ch in all_chs:
        title = chapter_titles.get(ch, f"Chapter {ch}")
        chapter_ids[ch] = insert_chapter(ch, title)

    # ── Pass 2: Extract each group ────────────────────────────────────────────
    groups = _group_labels(labels)

    if progress_callback:
        progress_callback(f"Pass 2: Extracting {len(groups)} section(s)…", 0.35)

    for gi, group in enumerate(groups):
        ch  = group["chapter"]
        sec = group["section"]
        q_n = len(group["q_pages"])
        a_n = len(group["a_pages"])

        if progress_callback:
            progress_callback(
                f"Pass 2: Ch{ch} {sec.upper()} ({q_n}Q + {a_n}A pages)…",
                0.35 + gi / max(len(groups), 1) * 0.60,
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
