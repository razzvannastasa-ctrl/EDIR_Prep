"""
PDF parser for EDiR_CORE.pdf.

Actual codepoints discovered by inspecting the PDF with PyMuPDF:
- Question marker : ASCII 0x3F '?' (Springer font maps visual-triangle → '?')
  pattern: '?\tQ<n>'
- Answer marker   : ASCII 'v' + whitespace + Q<n>  e.g. 'v Q1' or 'vQ1'
- Case boundary   : \\x07CORE\\n  (BEL = 0x07 precedes the word CORE)
- Case-number tag : \\x07C<n>\\n  (e.g. \\x07C1\\n, \\x07C2\\n)
- Bullet artefact : digit '5' followed by \\t or space at line-start
                    (Springer font maps visual-bullet → '5')
- Figure refs     : 'Fig.\\xa0X.Y' or 'Fig. X.Y'
"""

import re
import json
from pathlib import Path

try:
    import fitz
except ImportError:
    fitz = None

BASE_DIR   = Path(__file__).parent.parent
PDF_PATH   = BASE_DIR / "data" / "pdfs"  / "EDiR_CORE.pdf"
IMAGES_DIR = BASE_DIR / "data" / "page_images"

# ── Patterns (all verified against actual PDF bytes) ──────────────────────────
# '?' is the question marker (ASCII 0x3F, font-encoded visual triangle)
Q_PAT     = re.compile(r'\?\s*Q(\d+)', re.MULTILINE)

# 'v' is the answer marker (ASCII 0x76, font-encoded visual triangle)
A_PAT     = re.compile(r'(?<!\w)v\s*Q(\d+)', re.MULTILINE)

# Case-section boundary: \x07CORE\n, \x07CORE 2\n (numbered), or \x07C<n>\n
CASE_BOUNDARY = re.compile(r'\x07(?:CORE(?:\s*\d+)?|C\d+)\s*\n')

# Case-number tag: \x07C<n>\n or \x07CORE n\n  — strip from the top of each case block
CASE_NUM_TAG  = re.compile(r'^\x07(?:CORE\s*\d*|C\d+)\s*\n', re.MULTILINE)

# Answer-section boundary: same \x07CORE\n (or the long header variant)
ANS_BOUNDARY  = re.compile(
    r'(?:Clinical Oriented Reasoning Evaluation[^\n]*\n\s*\x07?CORE\s*\n|\x07CORE\s*\n)',
    re.IGNORECASE
)

# Figure references — non-breaking space (0xA0) or regular space
FIG_PAT   = re.compile(r'Fig\.[\s\xa0]+(\d+\.\d+)', re.IGNORECASE)

# ── Known page layout of EDiR_CORE.pdf (0-indexed) ───────────────────────────
CHAPTER_STRUCTURE = [
    {'num': 1,  'title': 'Abdominal Radiology',
     'header': 0,  'q_pages': (1,  4),  'ans_pages': (5,  6)},
    {'num': 2,  'title': 'Breast Radiology',
     'header': 7,  'q_pages': (8,  14), 'ans_pages': (15, 16)},
    {'num': 3,  'title': 'Cardiac Radiology',
     'header': 17, 'q_pages': (18, 19), 'ans_pages': (20, 21)},
    {'num': 4,  'title': 'Chest and Thorax Radiology',
     'header': 22, 'q_pages': (23, 24), 'ans_pages': (25, 26)},
    {'num': 5,  'title': 'Genitourinary Radiology',
     'header': 27, 'q_pages': (28, 30), 'ans_pages': (31, 31)},
    {'num': 6,  'title': 'Head and Neck',
     'header': 32, 'q_pages': (33, 38), 'ans_pages': (39, 40)},
    {'num': 8,  'title': 'Musculoskeletal Radiology',
     'header': 41, 'q_pages': (42, 49), 'ans_pages': (50, 51)},
    {'num': 9,  'title': 'Neuroradiology',
     'header': 52, 'q_pages': (53, 56), 'ans_pages': (57, 57)},
    {'num': 10, 'title': 'Pediatric Radiology',
     'header': 58, 'q_pages': (59, 63), 'ans_pages': (64, 65)},
]


# ── Low-level helpers ─────────────────────────────────────────────────────────

def _page_image_path(page_idx: int) -> str:
    return f"data/page_images/page_{page_idx:03d}.png"


def _get_page_texts(doc, start: int, end: int) -> list[tuple[int, str]]:
    return [(i, doc[i].get_text('text')) for i in range(start, end + 1)]


def _join(page_texts: list[tuple[int, str]]) -> tuple[str, list[tuple[int, int]]]:
    """
    Concatenate page texts.
    Returns (full_text, [(char_offset, page_idx), …]) sorted by offset.
    """
    full    = ''
    offsets = []
    for page_idx, text in page_texts:
        offsets.append((len(full), page_idx))
        full += text + '\n'
    return full, offsets


def _page_for(pos: int, offsets: list[tuple[int, int]]) -> int:
    page = offsets[0][1]
    for offset, pidx in offsets:
        if pos >= offset:
            page = pidx
        else:
            break
    return page


def _clean(text: str) -> str:
    """Strip common artefacts."""
    text = text.replace('\x07', '')              # BEL characters
    text = text.replace('\xa0', ' ')             # non-breaking space
    text = re.sub(r'https?://\S+', '', text)     # URLs
    text = re.sub(r'(?m)^\d+\s*$', '', text)    # lone number lines (page/chapter numbers)
    text = re.sub(r'(?m)^\t+\s*$', '', text)    # lone tab lines (footer artefacts)
    text = re.sub(r'(?m)^\.\s{2,}[^\n]*$', '', text)  # Springer image ref lines (". caption")
    text = re.sub(r'See\s+\.\s+Fig\.\s*[\d.]+\.?\s*', '', text)  # "See . Fig. X.Y."
    text = re.sub(r'(?m)^5[\t ]', '• ', text)   # bullet artefact '5\t'
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _parse_q_type_and_opts(raw: str) -> tuple[str, list[str], str]:
    """Return (q_type, options, cleaned_text)."""
    lower = raw.lower()
    if 'only one' in lower and ('correct' in lower or 'option' in lower):
        q_type = 'single_choice'
    elif 'multiple' in lower and 'correct' in lower:
        q_type = 'multiple_choice'
    else:
        q_type = 'free_text'

    options = []
    if q_type in ('single_choice', 'multiple_choice'):
        for m in re.finditer(r'\t(\d+)\.\t\s*([^\n]+)', raw):
            options.append(m.group(2).strip())

    clean = raw
    # Remove instruction lines — use [^\S\n]* so we don't eat the leading tab of option 1
    clean = re.sub(r'\(Only one (?:answer|option) is correct\.\)[^\S\n]*\n?', '', clean)
    clean = re.sub(r'\(Multiple (?:answers|correct).*?\)[^\S\n]*\n?', '', clean)
    clean = re.sub(r'(?m)^Multiple answers may be correct\.[^\S\n]*$\n?', '', clean)
    clean = re.sub(r'_{4,}[\s_]*', '', clean)          # blank underscores
    # Options block: permit optional leading tab (may be absent if preceding \n\t was eaten)
    clean = re.sub(r'(?m)^\t?\d+\.\t[ \t]*[^\n]+\n?', '', clean)
    clean = _clean(clean)
    return q_type, options, clean


def _find_figure_pages(q_text: str, page_texts: list[tuple[int, str]]) -> list[int]:
    refs = FIG_PAT.findall(q_text)
    fig_pages = []
    for ref in refs:
        for pidx, ptext in page_texts:
            if (f'Fig. {ref}' in ptext
                    or f'Fig.\xa0{ref}' in ptext
                    or f'.{ref}' in ptext):
                if pidx not in fig_pages:
                    fig_pages.append(pidx)
    return fig_pages


# ── Question-page parser ──────────────────────────────────────────────────────

def parse_question_pages(page_texts: list[tuple[int, str]]) -> list[dict]:
    """
    Returns list of case dicts:
      {'vignette': str, 'vignette_pages': [int], 'questions': [q_dict]}
    Each q_dict:
      {'number', 'text', 'type', 'options', 'pages'}
    """
    full, offsets = _join(page_texts)

    # ── Split on \x07CORE\n boundaries ───────────────────────────────────────
    # Segment 0 may be SC overflow (no Q1) or Case 1 (has Q1 at top).
    # Each boundary marks the START of a new case section.
    boundaries = [m.end() for m in CASE_BOUNDARY.finditer(full)]

    # Build raw segments: implicit segment 0 (before first boundary) + one per boundary
    raw_segments: list[tuple[int, str]] = []
    prev = 0
    for b in boundaries:
        raw_segments.append((prev, full[prev:b]))
        prev = b
    raw_segments.append((prev, full[prev:]))

    # Keep only segments that contain Q1
    case_slices: list[tuple[int, str]] = []
    for abs_start, seg in raw_segments:
        if Q_PAT.search(seg) and re.search(r'\?\s*Q1', seg):
            case_slices.append((abs_start, seg))

    if not case_slices:
        return []

    cases = []
    for abs_start, case_text in case_slices:
        # Strip \x07C<n> case-number tag
        case_text = CASE_NUM_TAG.sub('', case_text, count=1)

        first_q_m = Q_PAT.search(case_text)
        if not first_q_m:
            continue

        # Vignette = text before Q1
        vignette = _clean(case_text[:first_q_m.start()])
        vig_page = _page_for(abs_start, offsets)

        # Parse questions
        q_markers = list(Q_PAT.finditer(case_text))
        questions = []
        for qi, m in enumerate(q_markers):
            q_num      = int(m.group(1))
            q_raw_start = m.end()
            q_raw_end   = q_markers[qi + 1].start() if qi + 1 < len(q_markers) else len(case_text)
            q_raw       = case_text[q_raw_start:q_raw_end]

            q_type, options, q_text = _parse_q_type_and_opts(q_raw)

            # Which pages does this question appear on?
            abs_q_s = abs_start + m.start()
            abs_q_e = abs_start + q_raw_end - 1
            p_start = _page_for(abs_q_s, offsets)
            p_end   = _page_for(max(abs_q_s, abs_q_e), offsets)
            valid   = {pidx for pidx, _ in page_texts}
            q_pages = sorted({p for p in [p_start, p_end] if p in valid})

            # Add pages containing referenced figures
            for fp in _find_figure_pages(q_raw, page_texts):
                if fp not in q_pages:
                    q_pages.append(fp)

            questions.append({
                'number':  q_num,
                'text':    q_text,
                'type':    q_type,
                'options': options,
                'pages':   sorted(q_pages),
            })

        cases.append({
            'vignette':       vignette,
            'vignette_pages': [vig_page],
            'questions':      questions,
        })

    return cases


# ── Answer-page parser ────────────────────────────────────────────────────────

def parse_answer_pages(page_texts: list[tuple[int, str]]) -> list[dict]:
    """
    Returns list of per-case answer dicts:
      [{q_num: {'text': str, 'explanation': str}}, …]
    """
    full, _ = _join(page_texts)

    # Find start of CORE answer section
    core_m = ANS_BOUNDARY.search(full)
    if core_m:
        core_start = core_m.end()
    else:
        first_a = A_PAT.search(full)
        core_start = first_a.start() if first_a else 0

    core_text = full[core_start:]

    # Split on sub-case boundaries (same pattern as question pages)
    sub_bounds = [m.end() for m in CASE_BOUNDARY.finditer(core_text)]

    sections: list[str] = []
    prev = 0
    for b in sub_bounds:
        sections.append(core_text[prev:b])
        prev = b
    sections.append(core_text[prev:])

    all_answers: list[dict] = []
    for section in sections:
        section = CASE_NUM_TAG.sub('', section, count=1)

        markers = list(A_PAT.finditer(section))
        if not markers:
            continue  # skip header-only segments (e.g. just \x07C1\n)

        case_ans: dict[int, dict] = {}
        for ai, m in enumerate(markers):
            q_num = int(m.group(1))
            start = m.end()
            end   = markers[ai + 1].start() if ai + 1 < len(markers) else len(section)
            raw   = section[start:end].strip()

            exp_m = re.search(r'\nExplanation\s*\n', raw, re.IGNORECASE)
            if exp_m:
                ans_text    = raw[:exp_m.start()].strip()
                explanation = raw[exp_m.end():].strip()
            else:
                ans_text    = raw
                explanation = ''

            case_ans[q_num] = {
                'text':        _clean(ans_text),
                'explanation': _clean(explanation),
            }
        all_answers.append(case_ans)

    return all_answers


# ── Main entry point ──────────────────────────────────────────────────────────

def run_parser(progress_callback=None):
    """
    Parse EDiR_CORE.pdf → SQLite.
    progress_callback(msg: str, fraction: float)
    Returns (success: bool, message: str).
    """
    if fitz is None:
        return False, "PyMuPDF (fitz) is not installed. Run: pip install pymupdf"
    if not PDF_PATH.exists():
        return False, f"PDF not found: {PDF_PATH}\nCopy EDiR_CORE.pdf into data/pdfs/."

    from core.database import (
        init_db, clear_all, insert_chapter,
        insert_case, insert_question, insert_answer,
    )

    init_db()
    clear_all()
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    doc         = fitz.open(str(PDF_PATH))
    total_pages = len(doc)

    # ── 1. Render all pages as PNG ────────────────────────────────────────────
    if progress_callback:
        progress_callback("Rendering pages as images…", 0.0)

    for i in range(total_pages):
        out = IMAGES_DIR / f"page_{i:03d}.png"
        if not out.exists():
            mat = fitz.Matrix(2.5, 2.5)     # ≈ 180 DPI
            pix = doc[i].get_pixmap(matrix=mat)
            pix.save(str(out))
        if progress_callback:
            progress_callback(f"Rendering page {i + 1}/{total_pages}…",
                              (i + 1) / total_pages * 0.4)

    # ── 2. Parse each chapter ─────────────────────────────────────────────────
    for ch_idx, ch in enumerate(CHAPTER_STRUCTURE):
        if progress_callback:
            frac = 0.4 + ch_idx / len(CHAPTER_STRUCTURE) * 0.6
            progress_callback(f"Parsing: {ch['title']}…", frac)

        chapter_id = insert_chapter(ch['num'], ch['title'])

        q_texts   = _get_page_texts(doc, ch['q_pages'][0],   ch['q_pages'][1])
        ans_texts = _get_page_texts(doc, ch['ans_pages'][0], ch['ans_pages'][1])

        cases       = parse_question_pages(q_texts)
        all_answers = parse_answer_pages(ans_texts)

        ans_imgs = [_page_image_path(i)
                    for i in range(ch['ans_pages'][0], ch['ans_pages'][1] + 1)]

        # Align answer groups to the last N cases (some chapters have
        # unmarked answers for early cases, marked answers for later ones)
        ans_offset = max(0, len(cases) - len(all_answers))

        for case_idx, case_data in enumerate(cases):
            if not case_data['questions']:
                continue

            case_id = insert_case(chapter_id, case_idx + 1, case_data['vignette'])
            ans_idx = case_idx - ans_offset
            case_answers = all_answers[ans_idx] if ans_idx >= 0 else {}

            for q in case_data['questions']:
                q_num  = q['number']
                q_imgs = [_page_image_path(p) for p in q['pages']]

                q_id = insert_question(
                    case_id, q_num, q['text'], q['type'],
                    q['options'] if q['options'] else None,
                    q_imgs,
                )

                ans = case_answers.get(q_num, {})
                insert_answer(
                    q_id,
                    ans.get('text', ''),
                    None,
                    ans.get('explanation', ''),
                    ans_imgs,
                )

    doc.close()
    return True, "Parsing complete."
