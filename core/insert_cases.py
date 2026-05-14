"""
Insert EDiR cases from a Claude-generated JSON file into the database,
extracting images from the source PDF via PyMuPDF.

Usage:
    python -m core.insert_cases <cases.json> <book.pdf>
    python -m core.insert_cases <cases.json>          # skips image extraction
"""

import json
import re
import sys
from pathlib import Path

try:
    import fitz
except ImportError:
    fitz = None

from core.database import (
    get_next_case_number,
    insert_case,
    insert_question,
    insert_answer,
)

CROPS_DIR = Path(__file__).parent.parent / "data" / "crops"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:30]


def _extract_image(doc, page_idx: int, img_index: int, out_path: Path) -> bool:
    if out_path.exists():
        return True
    try:
        images = doc[page_idx].get_images(full=True)
        if img_index >= len(images):
            print(f"  Warning: page {page_idx} has {len(images)} images, index {img_index} out of range")
            return False
        xref = images[img_index][0]
        pix = fitz.Pixmap(doc, xref)
        if pix.colorspace and pix.colorspace.n > 3:
            pix = fitz.Pixmap(fitz.csRGB, pix)
        try:
            pix.save(str(out_path))
        except Exception:
            # Handles separation/spot-colour channels (e.g. CMYK-Black) that fail
            # direct PNG save — convert to RGB first.
            pix = fitz.Pixmap(fitz.csRGB, pix)
            pix.save(str(out_path))
        return True
    except Exception as e:
        print(f"  Warning: could not extract image p{page_idx} i{img_index}: {e}")
        return False


def _resolve_images(img_refs: list, doc, source_slug: str) -> list[str]:
    """Resolve image refs to filenames, extracting from PDF if doc is available."""
    filenames = []
    for ref in (img_refs or []):
        page = ref.get("page")
        idx = ref.get("img_index", 0)
        if page is None:
            continue
        fname = f"{source_slug}_p{page:03d}_i{idx:02d}.png"
        out_path = CROPS_DIR / fname
        rel_path = f"data/crops/{fname}"
        if doc:
            if _extract_image(doc, page, idx, out_path):
                filenames.append(rel_path)
        else:
            filenames.append(rel_path)
    return filenames


def insert_cases(cases: list, pdf_path: str | None = None) -> tuple[int, int]:
    """Insert cases into DB. Returns (cases_inserted, questions_inserted)."""
    doc = None
    if pdf_path:
        if not fitz:
            print("Warning: PyMuPDF not installed — images will not be extracted.")
        else:
            try:
                doc = fitz.open(pdf_path)
                print(f"Opened PDF: {pdf_path} ({len(doc)} pages)")
            except Exception as e:
                print(f"Warning: could not open PDF — images will not be extracted: {e}")

    CROPS_DIR.mkdir(parents=True, exist_ok=True)

    n_cases = 0
    n_questions = 0

    for i, case in enumerate(cases):
        chapter_id    = case.get("chapter_id")
        chapter_match = case.get("chapter_match", "close")
        source        = case.get("source", "Unknown")
        section       = case.get("section", "core")
        vignette      = case.get("clinical_vignette", "")
        source_slug   = _slug(source)

        if not chapter_id:
            print(f"  [{i+1}] Skipping case with no chapter_id")
            continue

        case_number = get_next_case_number(chapter_id, section)
        case_id = insert_case(
            chapter_id, case_number, vignette,
            section=section, source=source, chapter_match=chapter_match,
        )
        n_cases += 1

        questions = case.get("questions", [])
        for q in questions:
            q_number = q.get("q_number", 1)
            q_text   = q.get("question_text", "")
            q_type   = q.get("q_type", "free_text")
            options  = q.get("options")
            q_images = _resolve_images(q.get("page_images", []), doc, source_slug)

            ans      = q.get("answer", {})
            a_text   = ans.get("answer_text")
            a_correct = ans.get("correct_options")
            a_expl   = ans.get("explanation", "")
            a_images = _resolve_images(ans.get("page_images", []), doc, source_slug)

            q_id = insert_question(case_id, q_number, q_text, q_type, options, q_images)
            insert_answer(q_id, a_text or "", a_correct, a_expl, a_images)
            n_questions += 1

        print(f"  [{i+1}/{len(cases)}] chapter_id={chapter_id} | {section.upper()} "
              f"case {case_number} ({len(questions)}q) — {chapter_match}")

    if doc:
        doc.close()

    return n_cases, n_questions


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m core.insert_cases <cases.json> [book.pdf]")
        sys.exit(1)

    json_path = Path(sys.argv[1])
    pdf_path  = sys.argv[2] if len(sys.argv) > 2 else None

    raw = json.loads(json_path.read_text(encoding="utf-8"))
    cases = raw if isinstance(raw, list) else raw.get("cases", [])

    print(f"Loaded {len(cases)} cases from {json_path.name}")
    n_cases, n_q = insert_cases(cases, pdf_path)
    print(f"\nDone: {n_cases} cases, {n_q} questions inserted.")


if __name__ == "__main__":
    main()
