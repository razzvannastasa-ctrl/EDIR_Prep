# EDiR Book Import — Prompts & Workflow Reference

*Used when processing books directly in a Claude conversation (not via the automated pipeline).*

---

## Workflow Overview

1. User provides PDF path (or shares the file). Claude reads it directly.
2. User specifies: book name (source), import type (MRQ / CORE / SC), any book-specific instructions
   (e.g. "content starts at page 17", "TOC is pages 5–12", "skip front matter").
3. Claude reads the TOC (from bookmarks, or from the printed TOC pages if specified, or by scanning headings).
4. Claude processes the book chapter by chapter, generating cases in JSON.
5. A simple insertion script (`core/insert_cases.py`) inserts the JSON into the DB and extracts images.

---

## DB Chapter List (run at start of each session)

```python
from core.database import get_chapters
chapters = get_chapters()
for ch in chapters:
    print(ch["id"], ch["number"], ch["title"])
```

Chapter assignment rules (per case):
- `"exact"` — new case topic maps clearly to an existing chapter title
- `"close"` — related but not identical; assign to closest match
- `"forced"` — no good match; assign to nearest and flag it
- `null` — content is front matter, index, contributor list, or otherwise not a real case → **skip it, output nothing**

---

## Output JSON Schema (all types)

```json
[
  {
    "chapter_id": 5,
    "chapter_match": "exact",
    "source": "Book Title Here",
    "section": "core",
    "clinical_vignette": "A 52-year-old woman...",
    "questions": [
      {
        "q_number": 1,
        "question_text": "Describe the key findings.",
        "q_type": "free_text",
        "options": null,
        "page_images": [{"page": 23, "img_index": 0}],
        "answer": {
          "answer_text": "- Finding one\n- Finding two",
          "correct_options": null,
          "explanation": "...",
          "page_images": []
        }
      },
      {
        "q_number": 4,
        "question_text": "What is the most likely diagnosis?\n\n1. ...\n2. ...\n3. ...\n4. ...\n5. ...",
        "q_type": "single_choice",
        "options": ["...", "...", "...", "...", "..."],
        "page_images": [],
        "answer": {
          "answer_text": "Correct option text",
          "correct_options": null,
          "explanation": "...",
          "page_images": []
        }
      }
    ]
  }
]
```

For MRQ: `"section": "mrq"`, no `clinical_vignette` (or empty string), all questions `"q_type": "multiple_choice"`,
`"answer_text": null`, `"correct_options": [0-based indices]`.

For SC: `"section": "sc"`.

For CORE: `"section": "core"`.

Image refs: `{"page": <0-based pdf page>, "img_index": <0-based index of image on that page>}`.
The insertion script uses these to extract the actual image via PyMuPDF.

**Image inclusion rule:** Include ALL clinical images (any image ≥ 200 px in either dimension) — never select a representative subset.
- All clinical images from **question pages** → question `page_images`.
- All clinical images from **answer pages** → answer `page_images`.
- If an answer page contains a supplementary figure that relates to a specific sub-question, it still goes in that sub-question's answer `page_images` — do not reassign it to the question block.

**Important:** `page_images` must be stored as `"data/crops/filename.png"` (relative path with `data/crops/` prefix), not a bare filename. The app's `_load_images()` function filters out any path that does not contain the string `"crops"`, so bare filenames are silently ignored and no image is shown.

---

## CORE Cases Prompt

**Context:** You are a radiology education expert specialising in the European Diploma in Radiology (EDiR) exam.
You are reading a radiology case book directly. The text extracted from this book is authoritative — treat it
as ground truth. Images are the actual embedded figures from the book seen in their original context.

**Chapter assignment:** Before generating each case, assign it to the single most appropriate chapter from the
DB chapter list provided. If the content is front matter, an index, a contributor list, or otherwise not a
real educational case, output nothing for it (skip silently).

**CORE CASE FORMAT**

**Pre-drafting scan (do this before writing any questions):** Read the full answer section for the case and look for:
- Structured differential lists or tables → consider `multiple_choice` for Q3 or Q4 ("Which of the following are recognised differential diagnoses / causes of X?")
- Complication, classification, or aetiology lists → consider adding Q6 or Q7
- Multi-step management plans → use `free_text` for Q5 rather than `single_choice`
This scan must happen before you commit to a question structure — do not fill in the template top-to-bottom without checking what the source offers.

1. **Clinical vignette** — one paragraph, ≤ 4 sentences. Patient age/sex, presenting complaint, imaging modality.
   Do NOT reveal the diagnosis.

2. **Questions (4–7):**
   - Q1: "Describe the key findings." `[free_text]` — 3–6 bullet points from the primary modality.
   - Q2: "Describe the key normal and abnormal findings." `[free_text]` — 4–8 bullet points, second modality (if present).
   - Q3: Localising / characterising question `[free_text]` — 1–3 precise statements. OR: "Which of the following are recognised differential diagnoses / causes / features of X?" `[multiple_choice]` — if the source provides a structured differential table or list at this point in the case before the diagnosis is named.
   - Q4: Diagnosis or differential diagnosis. `[single_choice | multiple_choice | free_text]`
     - `single_choice`: "What is your diagnosis?" — use when the source names one clear principal diagnosis with plausible alternatives. Correct option = textbook diagnosis; 4 plausible differentials as distractors.
     - `multiple_choice`: "Which of the following are recognised differential diagnoses?" — use when the source provides 3+ named differentials in a structured list or table worth testing independently of the diagnosis question.
     - `free_text`: "List the top 3 differential diagnoses." — if the source gives a ranked narrative list rather than a single answer.
     - Do NOT default to `single_choice` without first checking whether the source supports a richer `multiple_choice` differential question.
   - Q5: Management or next step. `[single_choice | multiple_choice | free_text]`
     - `single_choice`: single best next action, 5 options — use when one action clearly precedes all others.
     - `multiple_choice`: "Which of the following are appropriate management steps?" — if multiple actions are correct simultaneously.
     - `free_text`: "Outline the management." — if the source gives a multi-step plan not reducible to a single correct option.
   - Q6/Q7 (optional): secondary finding, complication, aetiology, or classification. `[single_choice | multiple_choice | free_text]` — add whenever the source provides a structured list of complications, causes, or classification features that are educationally valuable and not already covered by Q3–Q5.

3. **Answers:**
   - `free_text`: short noun phrases, one finding per line, no full stop.
   - `single_choice`: `answer_text` = text of correct option; `correct_options` = null.
   - `multiple_choice`: `correct_options` = 0-based indices; `answer_text` = null.
   - Explanation (2–5 sentences): WHY findings → diagnosis, pathophysiology, clinical pearl.

4. **Options** (choice questions): always exactly 5, listed as "1. …\n2. …" in the question body AND in the options array.

**Distractor quality rule:**
- Incorrect options must be plausible, same-domain alternatives, not random unrelated items.
- Prefer distractors that are clinically or radiologically adjacent to the topic but clearly unsupported by the source.
- For management questions, wrong options should be plausible but inappropriate next steps.
- For risk-factor, complication, classification, or feature-list questions, wrong options should come from the same clinical category but must not be listed or implied by the source.
- Avoid silly or obviously unrelated distractors unless the source topic genuinely offers no reasonable alternatives.
- Do not use a distractor that is true from general medical knowledge if it would make the question ambiguous but is not supported by the source.

**Anti-hallucination rules:**
- The textbook's model answer is authoritative for findings and diagnosis. Do NOT second-guess it.
- If a finding is in the text but not clearly visible in the image, base the answer on the text and note this briefly in the explanation.
- If neither the text nor the image supports a finding, omit it. A shorter accurate case beats a padded fabricated one.
- Q1/Q2 may return fewer bullets than the stated range if the source genuinely supports fewer — do not pad.
- Do NOT add facts, figures, classifications, or statements not present in the extracted book content.
  If the source is insufficient to explain an option, say so briefly rather than drawing on outside knowledge.

**Style:** British English clinical register. ST4–ST7 level. Do not invent findings. Multiple source cases → multiple output case objects.

---

## Short Cases Prompt

**Context:** Same as CORE above. Text is authoritative. Images are native embedded figures.

**Chapter assignment:** Same rules as CORE. Skip non-case content silently.

**SHORT CASE FORMAT**

A Short Case (SC) is a focused spot-diagnosis scenario. Typical length: 2–5 questions.

1. **Clinical vignette** — 1–3 sentences. Patient age/sex, brief complaint. Do NOT name the diagnosis or imaging modality.

2. **Questions:**
   - Q1 — ALWAYS: "Indicate the abnormality." `[free_text]`
     Answer: one sentence — key abnormal finding + location.
   - Q2 — "What is the most likely diagnosis?" `[single_choice, 5 options]`
     OR "Which of the following findings do you recognise?" `[multiple_choice, 5 options]`
     Use the textbook's stated diagnosis as the correct option; construct 4 plausible alternatives.
   - Q3 — Specificity / aetiology. `[single_choice, 5 options]`
     OR `[free_text]` if the source only has a narrative answer.
   - Q4 (optional) — Differential diagnosis. `[multiple_choice, 5 options]`
   - Q5 (optional) — Management. `[single_choice, 5 options]`

3. **Options:** always exactly 5. `single_choice` → `answer_text` = correct option text.

**Distractor quality rule:**
- Incorrect options must be plausible, same-domain alternatives, not random unrelated items.
- Prefer distractors that are clinically or radiologically adjacent to the topic but clearly unsupported by the source.
- For management questions, wrong options should be plausible but inappropriate next steps.
- For risk-factor, complication, classification, or feature-list questions, wrong options should come from the same clinical category but must not be listed or implied by the source.
- Avoid silly or obviously unrelated distractors unless the source topic genuinely offers no reasonable alternatives.
- Do not use a distractor that is true from general medical knowledge if it would make the question ambiguous but is not supported by the source.

4. **Explanation** (1–4 sentences): imaging features supporting diagnosis; why main distractors are excluded.

**Anti-hallucination rules:** identical to CORE above. Q2/Q3 may be omitted if the source case is too brief
to support them — do not invent questions. Q1 is non-negotiable.

**Style:** British English. Each SC solvable in < 3 minutes. Do not invent findings. Multiple source cases → multiple output objects.

---

## MRQ Prompt

**Context:** You are a radiology education expert specialising in the EDiR exam. You are reading a radiology
theory/textbook chapter directly. The extracted text is your only authoritative source.

**Chapter assignment:** Assign the generated MRQ cluster to the single most appropriate DB chapter based on
its topic. If a section of text is front matter, an index, or non-educational prose, skip it silently.

**MRQ FORMAT RULES**

Each MRQ is a standalone multiple-select question — no shared clinical vignette.
Group the chapter content by topic; generate one cluster of related MRQs per topic.
Aim for 5–12 questions per chapter when content is rich; generate fewer if the source is thin.

1. **Question body** — one of:
   - Template A (image-based): "<Brief clinical context>.\n\nWhich of the following statements are correct regarding this image?"
   - Template B (knowledge): "Regarding <topic>, which of the following statements are correct?"

2. **Options** — always exactly 5, labelled a–e in the question body and in the options array.
   1–4 correct answers per question. Never all-correct or none-correct.
   Distractors must be plausible and at the same specificity level as the correct answers.

3. **Correct options** — 0-based indices, e.g. `[0, 2, 4]` for a, c, e.

4. **Explanation** — 3–6 sentences: why each correct option is right, why the main distractor is wrong, clinical/imaging pearl.

5. **Variety** — mix of: image interpretation, technical/protocol, guideline/classification, differential diagnosis, anatomy.

**Anti-hallucination rules:**
- Every option and every explanation must be grounded exclusively in the extracted chapter text.
- Do NOT add facts, statistics, classifications, or statements not present in the source.
- If the source does not support 5 distinct questions on a topic, generate fewer rather than inventing content.
- If the source is insufficient to explain a distractor, simplify the distractor rather than fabricating a justification.

**Style:** British English clinical register. ST4–ST7 / fellow level — requires integration, not simple recall.
Never "Which are NOT correct?" — always ask which ARE correct. Each question fully self-contained.

---

## Notes for Processing Large Books

- Process chapter by chapter. After each chapter, output the JSON block for that chapter.
- If a chapter is very long (> ~40 pages of dense theory for MRQ), split by heading/topic and process in two passes.
- For CORE/SC case books, each case is self-contained — natural split points exist.
- Ask clarifying questions at the START (after reading TOC), not mid-chapter.

---

## Book-Specific Tips: FRCR Long Cases (Cambridge FRCR Part 2B series)

### Page offset
- Front matter uses roman numerals; arabic page 1 = Introduction.
- To find the offset: run `get_text()` on PDF pages 15–22 and find which PDF page contains "Introduction" with arabic page marker "1".
- This book: arabic page 1 = PDF page 18 (1-based) = 0-based page 17. Offset = **printed page + 16 = 0-based PDF page**.
- Always verify with one spot-check before computing all ranges.

### Book structure
- Organised by **Packets** (1–10), each with 6 cases of mixed subspecialty content.
- Packet structure does NOT map to DB chapters — assign each case individually by content.
- Each case spans: 1–3 question pages (images) → optional "Answers to follow on page X" spacer → 1–3 answer pages (text + sometimes additional images).
- Spacer pages ("Answers to follow…") contain no clinical images, only decoratives — skip them entirely.

### Packet page ranges

| Packet | Cases | Printed pp | 0-based PDF pages |
|--------|-------|------------|-------------------|
| 1  | 6 | 9–42   | 25–58  |
| 2  | 6 | 43–76  | 59–92  |
| 3  | 6 | 77–114 | 93–130 |
| 4  | 6 | 115–159| 131–175|
| 5  | 6 | 160–194| 176–210|
| 6  | 6 | 195–230| 211–246|
| 7  | 6 | 231–268| 247–284|
| 8  | 6 | 269–303| 285–319|
| 9  | 6 | 304–336| 320–352|
| 10 | 6 | 337–377| 353–393|

Index starts at printed p.378 (0-based PDF p.394). Total 60 cases.

### Decorative image identification
- Every page contains 2 repeated decorative images: a logo (~173×51 px) and a horizontal rule (~405×15 px).
- Their xrefs change between sections of the book but their dimensions are consistent.
- **Rule: any image with either dimension < 200 px is decorative — skip it.**
- Clinical images are always large (typically 600–1400 px in both dimensions).
- Decoratives are NOT always at the end of the image list — sometimes they appear at index 0 and 1, pushing the clinical image to index 2. **Always check dimensions before assigning indices.**

### Extracting image indices (always do this before generating JSON)
```python
for p in [page_list]:
    imgs = doc[p].get_images(full=True)
    for i, img in enumerate(imgs):
        pix = fitz.Pixmap(doc, img[0])
        print(f'  [{i}] xref={img[0]} size={pix.width}x{pix.height}')
```
Then assign `img_index` to the indices of large images only.

### Answer-page images
- The textbook sometimes places additional educational figures (e.g. comparison cases, follow-up images) on the answer pages — these are labelled as Figures within the answer text.
- These are usually supplementary rather than the primary case images shown to the candidate.
- Include them in the **answer's** `page_images` if they directly illustrate a teaching point; exclude them from the question's `page_images`.
- CT confirmation images shown in the answer (e.g. "confirmed by CT, Figures X.Y.b and c") are useful to include in the answer's `page_images`.

### Chapter assignment judgment calls
- Neonatal/paediatric GU cases (e.g. posterior urethral valves in a 2-week-old) → assign to **Paediatric Radiology (id=10)**, not Genitourinary (id=5), when the patient age is clearly paediatric.
- Mixed cases (e.g. venous sinus thrombosis secondary to mastoiditis) → assign to the **primary imaging target**, not the source organ. Brain → Neuroradiology (id=9).
- Abdominal cases (small bowel ischaemia, stent ileus) → Abdominal Radiology (id=1).

### Q_type note
- This book's cases naturally split into: Q1/Q2 free_text findings, Q3 characterising free_text, Q4 diagnosis single_choice, Q5 management single_choice.
- Some cases only support 3 questions (e.g. Case 6: only one modality, diagnosis MCQ, management MCQ). Do not pad to 5 if the source doesn't support it.

---

## Book-Specific Tips: FRCR Long Cases v2 (`CORE2 cazuri scrise.pdf`)

### Source label
- Insert all cases from this book with `"source": "FRCR Long Cases v2"`.

### TOC and bookmarks
- The book uses **Exams** rather than Packets. Treat each Exam as one import batch.
- Ignore the PDF bookmarks for case navigation: they are generic scan bookmarks (`scan0001`, `scan0002`, etc.) and do not map reliably to case structure.
- Use the printed TOC, OCR text, and direct page inspection instead.
- Ignore the Appendix and Index for case generation.

### Exam page ranges

| Exam | Printed pp | 0-based PDF pages | Notes |
|------|------------|-------------------|-------|
| 1 | 1-30 | 9-36 | Six cases |
| 2 | 31-62 | 37-66 | Six cases |
| 3 | 63-94 | 67-96 | Six cases |
| 4 | 95-126 | 97-128 | Six cases, but skip colour plate pages and divider pages that are not part of the case |
| 5 | 127-156 | 129-154 | Six cases |
| 6 | 157-186 | 155-179 | Six cases |
| 7 | 187-218 | 180-204 | Six cases |

Appendix starts at printed p.219 / 0-based PDF p.205.
Index starts at printed p.223 / 0-based PDF p.209.

### Scanned-page image handling
- This PDF is OCR over scanned pages. PyMuPDF often exposes a large full-page background scan image on every page.
- Do **not** include full-page scan/background images in `page_images`, even though they are larger than 200 px.
- Include the actual clinical figure crops only: the smaller image objects corresponding to labelled figures (e.g. `1.1a`, `1.1b`, etc.).
- Use image dimensions and figure captions together. Background scans appear in two known sizes:
  - **Large background** (~900×1390 px): appears on earlier pages (Exam 1, first half of Exam 2). Usually at index 0.
  - **Small background** (~440×660 px): appears from roughly Exam 2 p.45 onwards and is consistent throughout Exams 3–7. Also usually at index 0. Despite being smaller than the large background, it is still a washed-out full-page scan, not a clinical image.
  - **Dark/black scan layer** (~1800×2100 or ~860×1170 px): solid dark overlays that appear occasionally. Skip these.
- If a page contains both a full-page scan and clinical figure crops, skip the full-page scan and include all clinical figure crops.
- Also skip OCR/layout artefacts: black masks, white margin blocks, footer/page-number strips, horizontal rules, cropped page borders, or any image object that contains no clinical anatomy/pathology.
- Some valid clinical image objects are composites containing two labelled figures on one cropped page region. Include those if the object clearly contains the labelled clinical figures.
- If the same figure page is duplicated by the scan/OCR layer, use only the cleaner duplicate once.
- Before generating JSON for this book, inspect candidate image objects visually or by dimensions/captions. Do not rely on the `>= 200 px` rule alone.
- **Visual inspection workflow** (for any ambiguous image): extract the PNG with `fitz.Pixmap(doc, xref).save(path)`, then use the Read tool to view it. This is the only reliable way to distinguish a clinical crop from a washed-out background at intermediate sizes.

### Case structure
- Each Exam contains six long cases.
- Each case usually follows: `Clinical details` -> `Imaging` -> figure pages -> `Observations and interpretations` -> `Principal diagnosis` -> `Differential diagnosis` -> `Further management` -> `Key points` -> references.
- Generate CORE cases from the actual case content only. Do not generate questions from references, notes pages, appendix material, index entries, or unrelated colour plate pages.
- Keep the FRCR report-style emphasis: observations, interpretation, principal diagnosis, short realistic differential, and practical further management.
