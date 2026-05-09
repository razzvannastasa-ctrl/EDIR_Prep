"""
New book import pipeline — additive, restartable.

Two public entry points:
  run_pass1(pdf_path, api_key, source, import_type, user_instructions, session_id, cb)
      → TOC extraction → chapter mapping → Pass 1 extraction per chapter
        Saves session file after every chapter; resumes automatically if called again.

  run_pass2(session_id, api_key, user_answers, gh_token, gh_repo, cb)
      → Pass 2 EDiR generation per chapter → DB insert + image crop → GitHub push
        Also resumes from last completed chapter.

Helper:
  get_clarification_questions(session_id) → list[str]
      Returns questions Claude raised during Pass 1 (shown to user before Pass 2).
"""

import hashlib
import json
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

from core.vision_import import _render, _img_msg, _parse_json, _crop_and_save, CROPS_DIR
from core.database import get_conn, get_chapters, get_next_case_number

SESSIONS_DIR = Path(__file__).parent.parent / "data" / "import_sessions"

_PASS1_ZOOM = 1.5
_CROP_ZOOM  = 2.0
_CHUNK_MRQ  = 25   # theory pages are independent; larger chunks ok
_CHUNK_CASE = 35   # send more at once so Q and A pages stay together


# ── Session helpers ────────────────────────────────────────────────────────────

def make_session_id(pdf_path: str, source: str, import_type: str) -> str:
    key = f"{pdf_path}|{source}|{import_type}"
    return hashlib.md5(key.encode()).hexdigest()[:12]


def load_session(session_id: str) -> dict | None:
    p = SESSIONS_DIR / f"{session_id}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def save_session(session_id: str, data: dict) -> None:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = time.time()
    (SESSIONS_DIR / f"{session_id}.json").write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def delete_session(session_id: str) -> None:
    p = SESSIONS_DIR / f"{session_id}.json"
    if p.exists():
        p.unlink()


def get_clarification_questions(session_id: str) -> list[str]:
    session = load_session(session_id)
    if not session:
        return []
    questions: list[str] = []
    for key in sorted(session.get("pass1_results", {}).keys(), key=int):
        questions.extend(session["pass1_results"][key].get("clarification_questions", []))
    return questions


# ── TOC extraction ─────────────────────────────────────────────────────────────

def _toc_from_bookmarks(doc) -> list[dict] | None:
    """Generic bookmark-based TOC. Returns [{number, title, start_page, end_page}] (0-based)."""
    raw = doc.get_toc()  # [(level, title, fitz_1based_page), ...]
    if not raw:
        return None
    chapters = [(t.strip(), p - 1) for lv, t, p in raw if lv == 1]
    if len(chapters) < 2:
        return None
    result = []
    for i, (title, start) in enumerate(chapters):
        end = chapters[i + 1][1] - 1 if i + 1 < len(chapters) else len(doc) - 1
        result.append({
            "number":     i + 1,
            "title":      title,
            "start_page": max(0, start),
            "end_page":   min(len(doc) - 1, end),
        })
    return result


def _toc_from_vision(client, doc) -> list[dict] | None:
    """Send first 35 pages to Claude to read the printed Table of Contents."""
    prompt = """\
These pages are from the beginning of a radiology textbook.
Find the Table of Contents and extract every chapter with its starting printed page number.

Return ONLY valid JSON — no prose:
{
  "toc_found": true,
  "printed_page_1_is_pdf_page": 17,
  "chapters": [
    {"number": 1, "title": "Chest Radiology", "start_printed_page": 1},
    {"number": 2, "title": "Abdominal Imaging", "start_printed_page": 45}
  ]
}
If no TOC is visible: {"toc_found": false}"""

    n = min(35, len(doc))
    imgs = [_img_msg(_render(doc, i, 1.0)) for i in range(n)]
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=4096,
                messages=[{"role": "user", "content": imgs + [{"type": "text", "text": prompt}]}],
            )
            data = _parse_json(resp.content[0].text)
            if not (data and data.get("toc_found") and data.get("chapters")):
                continue
            offset = data.get("printed_page_1_is_pdf_page", 1) - 1
            chs = sorted(data["chapters"], key=lambda c: c["start_printed_page"])
            result = []
            for i, ch in enumerate(chs):
                start = max(0, ch["start_printed_page"] - 1 + offset)
                end   = max(start, chs[i + 1]["start_printed_page"] - 2 + offset) \
                        if i + 1 < len(chs) else len(doc) - 1
                result.append({
                    "number":     ch.get("number", i + 1),
                    "title":      ch["title"],
                    "start_page": start,
                    "end_page":   min(len(doc) - 1, end),
                })
            return result
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


def _extract_toc(client, doc) -> list[dict] | None:
    toc = _toc_from_bookmarks(doc)
    return toc if toc else _toc_from_vision(client, doc)


# ── Chapter mapping ────────────────────────────────────────────────────────────

def _map_chapters(client, new_chapters: list[dict], existing_chapters) -> list[dict]:
    """One API call: map new book chapters → closest existing DB chapters."""
    existing = [{"id": c["id"], "number": c["number"], "title": c["title"]}
                for c in existing_chapters]
    new_list = [{"number": c["number"], "title": c["title"]} for c in new_chapters]

    prompt = f"""\
Map each chapter from the new radiology book to the closest existing database chapter, judged by anatomical topic.

New book chapters:
{json.dumps(new_list, indent=2)}

Existing database chapters:
{json.dumps(existing, indent=2)}

match field values:
- "exact"  : same body system / topic
- "close"  : related topic, minor differences
- "forced" : no good match, using closest available

Return ONLY valid JSON:
{{
  "mappings": [
    {{
      "new_number":       1,
      "new_title":        "Chest Radiology",
      "db_chapter_id":    3,
      "db_chapter_title": "Chest",
      "match":            "exact"
    }}
  ]
}}"""

    for attempt in range(3):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            data = _parse_json(resp.content[0].text)
            if data and "mappings" in data:
                return data["mappings"]
        except Exception:
            time.sleep(2 * (attempt + 1))

    # Hard fallback: force-assign everything to the first existing chapter
    fb_id    = existing[0]["id"]    if existing else 1
    fb_title = existing[0]["title"] if existing else "Unknown"
    return [{"new_number": c["number"], "new_title": c["title"],
              "db_chapter_id": fb_id, "db_chapter_title": fb_title, "match": "forced"}
            for c in new_chapters]


# ── Pass 1 prompts ─────────────────────────────────────────────────────────────

def _build_pass1_prompt(import_type: str, user_instructions: str,
                        chunk_idx: int, total_chunks: int) -> str:
    user_block = (
        f"\nAdditional instructions from the user:\n{user_instructions}\n"
        if user_instructions.strip() else ""
    )
    chunk_note = (
        f"\n[Chunk {chunk_idx + 1} of {total_chunks} for this chapter.]\n"
        if total_chunks > 1 else ""
    )
    preamble = user_block + chunk_note

    if import_type == "mrq":
        return f"""\
{preamble}These pages are from a radiology textbook.
Extract all educational content that can later be used to create exam-style questions.

Collect:
1. Key facts, definitions, clinical principles, imaging findings, protocols, classifications, guidelines.
2. All clinical images (X-ray, CT, MRI, US, histology) with bounding boxes — NOT text, logos, or diagrams.

Group extracted text by topic. Be as verbatim as possible.
Also list any ambiguities or questions you have about the content.

Return ONLY valid JSON — no prose outside the object:
{{
  "chapter_title": "your best guess at the chapter title",
  "content_blocks": [
    {{
      "topic":       "brief topic label",
      "text":        "verbatim extracted text",
      "page_offset": 0
    }}
  ],
  "images": [
    {{
      "index":       0,
      "page_offset": 0,
      "bbox":        {{"top": 0.1, "left": 0.05, "bottom": 0.6, "right": 0.95}},
      "description": "what the image shows",
      "context":     "what topic/concept this image illustrates"
    }}
  ],
  "clarification_questions": ["..."]
}}"""
    else:
        return f"""\
{preamble}These pages are from a radiology case book.
Cases typically have 1–3 image pages followed by 1–3 answer pages, but the layout may vary.

Extract every case with its clinical history, questions, and answers.
Match each question to its answer even if they are several pages apart.
Also locate all clinical images.

Return ONLY valid JSON — no prose outside the object:
{{
  "chapter_title": "your best guess at the chapter title",
  "cases": [
    {{
      "vignette": "clinical history / presentation",
      "questions": [
        {{
          "number":      1,
          "text":        "exact question text",
          "type":        "free_text",
          "options":     [],
          "answer":      "exact answer text",
          "explanation": "",
          "page_offset": 0
        }}
      ]
    }}
  ],
  "images": [
    {{
      "index":       0,
      "page_offset": 0,
      "bbox":        {{"top": 0.1, "left": 0.05, "bottom": 0.6, "right": 0.95}},
      "description": "what the image shows",
      "context":     "which case / question this image likely belongs to"
    }}
  ],
  "clarification_questions": []
}}"""


# ── Pass 2 prompts ─────────────────────────────────────────────────────────────

def _build_pass2_prompt(import_type: str, chapter_title: str,
                        content_text: str, image_list: str, n_images: int,
                        user_answers: str, user_instructions: str) -> str:
    user_block = (
        f"\nAdditional instructions from the user:\n{user_instructions}\n"
        if user_instructions.strip() else ""
    )
    answers_block = user_answers.strip() or "(none)"

    image_note = (
        f"\nAvailable images ({n_images} total):\n{image_list}\n"
        if n_images > 0 else "\nNo clinical images available for this chapter.\n"
    )

    image_ref_rule = (
        'For each question that references or should reference a clinical image, add '
        '"image_refs": [list of 0-based indices from the Available images list]. '
        'For questions with no image: "image_refs": [].'
        if n_images > 0 else
        'Set "image_refs": [] for all questions (no images available).'
    )

    if import_type == "mrq":
        return f"""\
You are a radiology education expert specialising in the European Diploma in Radiology (EDiR) exam.
You are given extracted content from a radiology textbook chapter.
Your task is to generate EDiR-style Multiple Response Questions (MRQs) from this content.
{user_block}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MRQ FORMAT RULES

Each MRQ is a standalone multiple-select question — no shared vignette.

1. QUESTION BODY — one of:
   Template A (image-based): "<Brief clinical context>.\\n\\nWhich of the following statements are correct regarding this image?"
   Template B (knowledge): "Regarding <topic>, which of the following statements are correct?"

2. OPTIONS — always exactly 5, labelled a–e in both the question body and the options array.
   1–4 correct answers. Never all-correct or none-correct.
   Distractors must be plausible and at the same specificity level as correct answers.

3. CORRECT OPTIONS — 0-based indices, e.g. [0, 2, 4] for a, c, e.

4. EXPLANATION — 3–6 sentences: why each correct option is right, why the main distractor is wrong, clinical/imaging pearl.

5. VARIETY — mix of: image interpretation, technical/protocol, guideline/classification, differential diagnosis, anatomy.
   Aim for 5–12 questions per chapter when content is rich.

6. IMAGE ASSOCIATION — {image_ref_rule}

STYLE
- British English clinical register.
- ST4–ST7 / fellow level — requires integration, not simple recall.
- Never "Which are NOT correct?" — always ask which ARE correct.
- Each question fully self-contained; no cross-references between questions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Chapter: {chapter_title}
User clarifications: {answers_block}
{image_note}
Extracted content:
{content_text}

Return ONLY valid JSON:
{{
  "questions": [
    {{
      "q_number":     1,
      "question_text":"...",
      "q_type":       "multiple_choice",
      "options":      ["a. ...", "b. ...", "c. ...", "d. ...", "e. ..."],
      "answer_text":  null,
      "correct_options": [0, 2],
      "explanation":  "...",
      "image_refs":   []
    }}
  ]
}}"""

    if import_type == "core":
        return f"""\
You are a radiology education expert specialising in the EDiR exam.
You are given extracted raw case content from a radiology textbook.
Reformat it into EDiR-style CORE Cases suitable for self-assessment.
{user_block}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CORE CASE FORMAT

1. CLINICAL VIGNETTE — one paragraph ≤ 4 sentences. Patient age/sex, presenting complaint,
   imaging modality. Do NOT reveal the diagnosis.

2. QUESTIONS (4–7):
   Q1: "Describe the key findings." [free_text] — 3–6 bullet points, first modality.
   Q2: "Describe the key normal and abnormal findings." [free_text] — 4–8 bullet points, second modality.
   Q3: Localising / characterising question. [free_text] — 1–3 precise statements.
   Q4: "What is your diagnosis?" [single_choice, 5 options] — correct + 4 plausible differentials.
   Q5: Management / next-step. [single_choice, 5 options]
   Q6/Q7 (optional): secondary finding, complication, or aetiology. [single_choice or multiple_choice]

3. ANSWERS
   free_text: short noun phrases, one finding per line (no full-stop).
   single_choice: answer_text = text of correct option; correct_options = null.
   multiple_choice: correct_options = 0-based indices; answer_text = null.
   Explanation (2–5 sentences): WHY findings → diagnosis, pathophysiology, clinical pearl.

4. OPTIONS (choice questions): always 5, listed as "1. …\\n2. …" in the question body.

5. IMAGE ASSOCIATION — {image_ref_rule}

STYLE
- British English clinical register.
- Do NOT invent findings absent from the source material.
- Q1–Q3 answerable at ST4 level; Q4–Q7 require integrated interpretation.
- Multiple source cases → multiple output case objects.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Chapter: {chapter_title}
User clarifications: {answers_block}
{image_note}
Extracted cases (raw):
{content_text}

Return ONLY valid JSON:
{{
  "cases": [
    {{
      "clinical_vignette": "...",
      "questions": [
        {{
          "q_number":      1,
          "question_text": "...",
          "q_type":        "free_text",
          "options":       null,
          "answer_text":   "...",
          "correct_options": null,
          "explanation":   "...",
          "image_refs":    []
        }}
      ]
    }}
  ]
}}"""

    # sc
    return f"""\
You are a radiology education expert specialising in the EDiR exam.
You are given extracted raw case content from a radiology case book.
Reformat it into EDiR-style Short Cases for self-assessment.
{user_block}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SHORT CASE FORMAT

A Short Case (SC) is a focused spot-diagnosis scenario. Typical length: 2–5 questions.

1. CLINICAL VIGNETTE — 1–3 sentences. Patient age/sex, brief complaint/data.
   Do NOT name the diagnosis or imaging modality.

2. QUESTIONS:
   Q1 — ALWAYS: "Indicate the abnormality." [free_text]
        Answer: one sentence — key abnormal finding + location. Mention annotated image if available.
   Q2 — "What is the most likely diagnosis?" [single_choice, 5 options]
        OR "Which of the following findings do you recognise?" [multiple_choice, 5 options]
        List options as "1. …\\n2. …" in body AND in options array (text only, no number prefix).
   Q3 — Specificity / aetiology. [free_text]
   Q4 (optional) — Differential diagnosis. [multiple_choice, 5 options]
   Q5 (optional) — Management. [single_choice or multiple_choice, 5 options]

3. OPTIONS: always 5. single_choice → answer_text = correct option text.
   multiple_choice → correct_options = 0-based indices.

4. EXPLANATION (1–4 sentences): imaging features supporting diagnosis; why distractors excluded.

5. IMAGE ASSOCIATION — {image_ref_rule}

STYLE
- Q1 MUST be "Indicate the abnormality." — non-negotiable.
- Each SC solvable in < 3 minutes.
- British English clinical register.
- Do NOT invent findings absent from the source.
- Multiple source cases → multiple case objects.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Chapter: {chapter_title}
User clarifications: {answers_block}
{image_note}
Extracted cases (raw):
{content_text}

Return ONLY valid JSON:
{{
  "cases": [
    {{
      "clinical_vignette": "...",
      "questions": [
        {{
          "q_number":      1,
          "question_text": "Indicate the abnormality.",
          "q_type":        "free_text",
          "options":       null,
          "answer_text":   "...",
          "correct_options": null,
          "explanation":   "...",
          "image_refs":    []
        }}
      ]
    }}
  ]
}}"""


# ── Pass 1 extraction per chapter ──────────────────────────────────────────────

def _pass1_chapter(client, doc, chapter: dict, import_type: str,
                   user_instructions: str) -> dict | None:
    """Extract raw content + image locations from all pages of one chapter."""
    start = chapter["start_page"]
    end   = chapter["end_page"]
    pages = list(range(start, min(end + 1, len(doc))))
    if not pages:
        return None

    chunk_size = _CHUNK_MRQ if import_type == "mrq" else _CHUNK_CASE
    overlap    = 3
    if len(pages) <= chunk_size:
        chunks = [pages]
    else:
        chunks = []
        i = 0
        while i < len(pages):
            chunks.append(pages[i: i + chunk_size])
            i += chunk_size - overlap

    all_blocks:  list[dict] = []
    all_cases:   list[dict] = []
    all_images:  list[dict] = []
    all_q:       list[str]  = []
    chapter_title = chapter["title"]
    chunk_pages_list: list[list[int]] = []
    global_img_idx = 0

    for ci, chunk in enumerate(chunks):
        page_imgs = [_img_msg(_render(doc, p, _PASS1_ZOOM)) for p in chunk]
        prompt    = _build_pass1_prompt(import_type, user_instructions, ci, len(chunks))

        data = None
        for attempt in range(3):
            try:
                resp = client.messages.create(
                    model="claude-sonnet-4-6", max_tokens=8192,
                    messages=[{"role": "user",
                               "content": page_imgs + [{"type": "text", "text": prompt}]}],
                )
                data = _parse_json(resp.content[0].text)
                if data:
                    break
            except Exception:
                time.sleep(2 * (attempt + 1))

        if not data:
            chunk_pages_list.append(chunk)
            continue

        chapter_title = data.get("chapter_title") or chapter_title
        chunk_pages_list.append(chunk)

        for img in data.get("images", []):
            img["index"]     = global_img_idx
            img["chunk_idx"] = ci
            global_img_idx  += 1
            all_images.append(img)

        all_blocks.extend(data.get("content_blocks", []))
        all_cases.extend(data.get("cases", []))
        all_q.extend(data.get("clarification_questions", []))
        time.sleep(0.1)

    result: dict = {
        "chapter_title":           chapter_title,
        "images":                  all_images,
        "chunk_pages":             chunk_pages_list,
        "clarification_questions": all_q,
    }
    if import_type == "mrq":
        result["content_blocks"] = all_blocks
    else:
        result["cases"] = all_cases
    return result


# ── Pass 2 generation per chapter ──────────────────────────────────────────────

def _pass2_chapter(client, pass1: dict, import_type: str,
                   user_answers: str, user_instructions: str) -> dict | None:
    """Generate EDiR-format cases/questions from Pass 1 extracted content."""
    chapter_title = pass1.get("chapter_title", "Unknown")
    images        = pass1.get("images", [])

    if import_type == "mrq":
        blocks = pass1.get("content_blocks", [])
        content_text = "\n\n".join(
            f"[{b['topic']}]\n{b['text']}" for b in blocks
        ) if blocks else "(no content extracted)"
    else:
        cases = pass1.get("cases", [])
        content_text = json.dumps(cases, indent=2) if cases else "(no cases extracted)"

    image_list = "\n".join(
        f"  [{img['index']}] {img.get('description','?')} — {img.get('context','')}"
        for img in images
    ) if images else "  (none)"

    prompt = _build_pass2_prompt(
        import_type, chapter_title, content_text,
        image_list, len(images), user_answers, user_instructions,
    )

    for attempt in range(3):
        try:
            resp = client.messages.create(
                model="claude-sonnet-4-6", max_tokens=8192,
                messages=[{"role": "user", "content": prompt}],
            )
            data = _parse_json(resp.content[0].text)
            if data:
                return data
        except Exception:
            time.sleep(2 * (attempt + 1))
    return None


# ── Image cropping ─────────────────────────────────────────────────────────────

def _crop_refs(image_refs: list[int], pass1_images: list[dict],
               chunk_pages: list[list[int]], doc,
               img_counter: dict[int, int], session_prefix: str) -> list[str]:
    """Crop images referenced by a generated question. Returns relative crop paths."""
    paths: list[str] = []
    for ref in image_refs:
        if not (0 <= ref < len(pass1_images)):
            continue
        img   = pass1_images[ref]
        ci    = img.get("chunk_idx", 0)
        p_off = img.get("page_offset", 0)
        bbox  = img.get("bbox", {})

        if ci >= len(chunk_pages) or p_off >= len(chunk_pages[ci]):
            continue

        pdf_page = chunk_pages[ci][p_off]
        idx      = img_counter[pdf_page]
        img_counter[pdf_page] += 1

        rel       = f"data/crops/{session_prefix}_p{pdf_page:03d}_img{idx:02d}.png"
        crop_path = Path(__file__).parent.parent / rel

        if _crop_and_save(doc, pdf_page, bbox, crop_path, zoom=_CROP_ZOOM):
            paths.append(rel)
    return paths


# ── DB insert helpers ──────────────────────────────────────────────────────────

def _insert_mrq(data: dict, chapter_id: int, source: str, chapter_match: str,
                pass1: dict, doc, img_counter: dict, session_prefix: str) -> tuple[int, list[str]]:
    from core.database import insert_case, insert_question, insert_answer
    questions = data.get("questions", [])
    if not questions:
        return 0, []

    case_num = get_next_case_number(chapter_id, "mrq")
    case_id  = insert_case(chapter_id, case_num, None, section="mrq",
                            source=source, chapter_match=chapter_match)

    pass1_imgs   = pass1.get("images", [])
    chunk_pages  = pass1.get("chunk_pages", [])
    all_crops: list[str] = []
    n = 0

    for q in questions:
        q_num    = int(q.get("q_number", n + 1))
        q_text   = (q.get("question_text") or "").strip()
        q_type   = q.get("q_type", "multiple_choice")
        options  = q.get("options") or None
        ans_text = q.get("answer_text") or ""
        correct  = q.get("correct_options")
        expl     = (q.get("explanation") or "").strip()
        refs     = q.get("image_refs", [])

        crops = _crop_refs(refs, pass1_imgs, chunk_pages, doc, img_counter, session_prefix)
        all_crops.extend(crops)

        q_id = insert_question(case_id, q_num, q_text, q_type, options, crops)
        insert_answer(q_id, ans_text, correct, expl, [])
        n += 1

    return n, all_crops


def _insert_cases(data: dict, chapter_id: int, section: str, source: str,
                  chapter_match: str, pass1: dict, doc,
                  img_counter: dict, session_prefix: str) -> tuple[int, int, list[str]]:
    from core.database import insert_case, insert_question, insert_answer
    cases = data.get("cases", [])
    if not cases:
        return 0, 0, []

    pass1_imgs  = pass1.get("images", [])
    chunk_pages = pass1.get("chunk_pages", [])
    all_crops: list[str] = []
    n_cases = n_qs = 0

    for case in cases:
        vignette = (case.get("clinical_vignette") or "").strip() or None
        case_num = get_next_case_number(chapter_id, section)
        case_id  = insert_case(chapter_id, case_num, vignette, section=section,
                                source=source, chapter_match=chapter_match)
        n_cases += 1

        for q in case.get("questions", []):
            q_num    = int(q.get("q_number", n_qs + 1))
            q_text   = (q.get("question_text") or "").strip()
            q_type   = q.get("q_type", "free_text")
            options  = q.get("options") or None
            ans_text = q.get("answer_text") or ""
            correct  = q.get("correct_options")
            expl     = (q.get("explanation") or "").strip()
            refs     = q.get("image_refs", [])

            crops = _crop_refs(refs, pass1_imgs, chunk_pages, doc, img_counter, session_prefix)
            all_crops.extend(crops)

            q_id = insert_question(case_id, q_num, q_text, q_type, options, crops)
            insert_answer(q_id, ans_text, correct, expl, [])
            n_qs += 1

    return n_cases, n_qs, all_crops


# ── Public entry points ────────────────────────────────────────────────────────

def run_pass1(pdf_path: str, api_key: str, source: str, import_type: str,
              user_instructions: str, session_id: str,
              progress_callback=None) -> tuple[bool, str]:
    """
    Extract TOC, map chapters to DB, and run Pass 1 extraction for every chapter.
    Saves progress after each chapter; call again with the same session_id to resume.
    """
    if anthropic is None:
        return False, "anthropic package not installed."
    if fitz is None:
        return False, "PyMuPDF not installed."
    if not api_key:
        return False, "No API key provided."

    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        return False, f"PDF not found: {pdf_path}"

    client = anthropic.Anthropic(api_key=api_key)

    session = load_session(session_id) or {
        "session_id":       session_id,
        "pdf_path":         str(pdf_path),
        "source":           source,
        "import_type":      import_type,
        "user_instructions": user_instructions,
        "created_at":       time.time(),
        "status":           "started",
        "toc":              None,
        "chapter_mapping":  None,
        "pass1_results":    {},
        "pass2_completed":  [],
        "user_answers":     "",
    }

    doc = fitz.open(str(pdf_path))
    try:
        # ── TOC ───────────────────────────────────────────────────────────────
        if not session.get("toc"):
            if progress_callback:
                progress_callback("Extracting table of contents…", 0.0)
            toc = _extract_toc(client, doc)
            if not toc:
                doc.close()
                return False, (
                    "Could not extract TOC. Make sure the PDF has bookmarks or a visible "
                    "Table of Contents in the first 35 pages. Add page-range hints in the "
                    "book-specific instructions field if needed."
                )
            session["toc"] = toc
            session["status"] = "toc_done"
            save_session(session_id, session)

        toc: list[dict] = session["toc"]

        # ── Chapter mapping ───────────────────────────────────────────────────
        if not session.get("chapter_mapping"):
            if progress_callback:
                progress_callback("Mapping chapters to database…", 0.05)
            existing = get_chapters()
            mapping  = _map_chapters(client, toc, existing)
            session["chapter_mapping"] = mapping
            session["status"] = "mapping_done"
            save_session(session_id, session)

        # ── Pass 1 per chapter ────────────────────────────────────────────────
        done = set(session["pass1_results"].keys())
        total = len(toc)

        for ci, chapter in enumerate(toc):
            key = str(ci)
            if key in done:
                if progress_callback:
                    progress_callback(
                        f"Ch{chapter['number']} {chapter['title'][:30]!r} — already extracted",
                        (ci + 1) / total * 0.95,
                    )
                continue

            n_pages = chapter["end_page"] - chapter["start_page"] + 1
            if progress_callback:
                progress_callback(
                    f"Pass 1 — Ch{chapter['number']}: {chapter['title'][:40]!r} ({n_pages} pages)…",
                    ci / total * 0.95,
                )

            result = _pass1_chapter(client, doc, chapter, import_type, user_instructions)
            if result:
                session["pass1_results"][key] = result
                save_session(session_id, session)

        session["status"] = "pass1_complete"
        save_session(session_id, session)

    finally:
        doc.close()

    n_chs  = len(session["pass1_results"])
    n_imgs = sum(len(r.get("images", [])) for r in session["pass1_results"].values())
    n_q    = len(get_clarification_questions(session_id))

    if progress_callback:
        progress_callback("Pass 1 complete.", 1.0)

    return True, (
        f"Pass 1 complete — {n_chs} chapter(s), {n_imgs} image(s) found. "
        f"{n_q} clarification question(s) from Claude."
    )


def run_pass2(session_id: str, api_key: str, user_answers: str,
              gh_token: str, gh_repo: str,
              progress_callback=None) -> tuple[bool, str]:
    """
    Generate EDiR-format content per chapter, insert into DB, push to GitHub.
    Resumes from last completed chapter if called again with the same session_id.
    """
    if anthropic is None:
        return False, "anthropic package not installed."
    if fitz is None:
        return False, "PyMuPDF not installed."
    if not api_key:
        return False, "No API key provided."

    session = load_session(session_id)
    if not session:
        return False, "Session not found. Run Pass 1 first."
    if session.get("status") not in ("pass1_complete", "pass2_partial"):
        return False, f"Cannot run Pass 2 in state '{session.get('status')}'."

    pdf_path = Path(session["pdf_path"])
    if not pdf_path.exists():
        return False, f"PDF not found: {pdf_path}"

    session["user_answers"] = user_answers
    save_session(session_id, session)

    client      = anthropic.Anthropic(api_key=api_key)
    import_type = session["import_type"]
    source      = session["source"]
    user_instr  = session.get("user_instructions", "")
    toc: list[dict] = session["toc"]
    pass1_results   = session.get("pass1_results", {})
    pass2_done      = set(session.get("pass2_completed", []))
    mapping         = {m["new_number"]: m for m in session.get("chapter_mapping", [])}

    existing_ch = {c["number"]: c["id"] for c in get_chapters()}
    fb_ch_id    = next(iter(existing_ch.values()), 1)

    CROPS_DIR.mkdir(parents=True, exist_ok=True)
    img_counter: dict[int, int] = defaultdict(int)
    session_prefix = session_id[:8]

    doc = fitz.open(str(pdf_path))
    total      = len(pass1_results)
    n_cases    = n_qs = 0
    all_crops: list[str] = []

    try:
        for ci, chapter in enumerate(toc):
            key = str(ci)
            if key not in pass1_results:
                continue
            if key in pass2_done:
                if progress_callback:
                    progress_callback(
                        f"Ch{chapter['number']} — already generated",
                        (ci + 1) / total * 0.9,
                    )
                continue

            ch_num     = chapter["number"]
            ch_map     = mapping.get(ch_num, {})
            db_ch_id   = ch_map.get("db_chapter_id") or fb_ch_id
            ch_match   = ch_map.get("match", "forced")

            if progress_callback:
                progress_callback(
                    f"Pass 2 — Ch{ch_num}: {chapter['title'][:40]!r}…",
                    ci / total * 0.9,
                )

            pass1 = pass1_results[key]
            data  = _pass2_chapter(client, pass1, import_type, user_answers, user_instr)
            if not data:
                continue

            if import_type == "mrq":
                n_q, crops = _insert_mrq(data, db_ch_id, source, ch_match,
                                         pass1, doc, img_counter, session_prefix)
                n_cases += 1 if n_q > 0 else 0
                n_qs    += n_q
            else:
                nc, nq, crops = _insert_cases(data, db_ch_id, import_type, source, ch_match,
                                              pass1, doc, img_counter, session_prefix)
                n_cases += nc
                n_qs    += nq
            all_crops.extend(crops)

            pass2_done.add(key)
            session["pass2_completed"] = list(pass2_done)
            session["status"] = "pass2_partial"
            save_session(session_id, session)
            time.sleep(0.1)

        session["status"] = "pass2_complete"
        save_session(session_id, session)

    finally:
        doc.close()

    # ── GitHub push ────────────────────────────────────────────────────────────
    if gh_token and gh_repo:
        if progress_callback:
            progress_callback("Pushing to GitHub…", 0.95)
        try:
            from core.github_sync import push_db, push_image
            from core.database import DB_PATH
            push_db(gh_token, gh_repo, DB_PATH)
            for rel in all_crops:
                local = Path(__file__).parent.parent / rel
                if local.exists():
                    try:
                        push_image(gh_token, gh_repo, local, rel)
                    except Exception:
                        pass
        except Exception:
            pass

    if progress_callback:
        progress_callback("Done.", 1.0)

    return True, (
        f"Import complete — {n_cases} case(s), {n_qs} question(s) added from '{source}'."
    )
