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

## Mandatory Per-Batch Cycle

For every book import, process batches one by one. Do not merge the work for several batches into a single
read/draft/validate/insert pass.

For EACH batch, the cycle is:
1. Re-read the relevant parts of `import_prompts.md`.
2. Extract the text and image/page structure for that batch only.
3. Understand the source content for that batch before drafting.
4. Draft the JSON for that batch only.
5. Validate every rule that applies to that batch: source label, chapter routing, case/question counts,
   image refs, original answer pages, no diagnosis leakage, option count, correct-answer count distribution,
   answer-position spread, and source-grounding.
6. Insert that validated batch into the DB, or explicitly keep it as a validated JSON batch if the user has
   asked to defer insertion.
7. Only then move to the next batch.

If validation fails, revise the same batch before moving on. A later batch must not be used to compensate for
unvalidated or weak work in an earlier batch.

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
    "original_answer_pages": [28, 29],
    "article_summary": null,
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
        "question_text": "What is the most likely diagnosis?",
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

**SC/CORE image-staging rule:** "All clinical images" does not mean attaching every question-page image to every question.
- Before drafting any SC/CORE case with more than one modality, phase, sequence, plane, time-point, or image group, create a brief case image map:
  `source page/panel -> modality or phase -> intended question number -> question.page_images -> answer.page_images`.
  Draft the questions from that map, not from a page-wide image list.
- If a case has multiple modalities, phases, sequences, planes, time-points, or clearly separate image groups, assign images to the specific question that asks about that group.
- Examples: CT-only findings question gets CT images only; CTA-only findings question gets CTA images only; MRI question gets MRI images only; radiograph question gets radiograph images only; follow-up question gets follow-up images only.
- Preserve the learner's sequence. If Q1 asks for the initial CT and Q2 asks for CTA, Q1 must show only the CT images and Q2 must show the CTA images. Do not place CT+CTA together on Q1 unless Q1 explicitly asks for a combined CT/CTA assessment.
- A staged CT/CTA, radiograph/CT, US/MRI, CT/MRI, angiography/CT, baseline/follow-up, pre-/post-contrast, or phase-specific case should not have identical `page_images` on each findings question unless the stem explicitly asks the learner to compare the same image set.
- A modality-specific findings question must not have empty `page_images` if the relevant images exist elsewhere in the same case.
- Do not hide a missing question image by placing the relevant image only in `answer.page_images`. If the question asks the learner to interpret that image group, the non-answer-revealing question-side image(s) must be in that question's `page_images`.
- Use captions, panel labels, answer text, and visual inspection of rendered pages to map PyMuPDF image indices to the correct question. Do not rely on extraction order alone when image groups are ambiguous.
- Answer-page labelled, annotated, repeat, or explanatory images belong in `answer.page_images` for the relevant question, not in the pre-diagnosis question image block.
- **Hard validation before insertion:** for every staged SC/CORE case, check the case image map against the final JSON. Each image-dependent question must have the correct non-empty `page_images`, staged findings questions must not accidentally share the same full image set, and no later modality/phase image may be stranded under an earlier question.

**Important:** `page_images` must be stored as `"data/crops/filename.png"` (relative path with `data/crops/` prefix), not a bare filename. The app's `_load_images()` function filters out any path that does not contain the string `"crops"`, so bare filenames are silently ignored and no image is shown.

**Original answer-page screenshots (SC/CORE only):**
- For every `sc` and `core` case from a case book, add case-level `"original_answer_pages": [<0-based PDF page>, ...]`.
- These are full source answer/model-answer/discussion pages, not embedded figure refs. Do not include `img_index`.
- Include the complete answer span: model answer, diagnosis, observations/interpretation, teaching text, pearls/pitfalls, and case discussion pages that belong to that source case.
- Exclude question-only pages, front matter, title/divider pages, appendix/index pages, and unrelated reference-only pages.
- For MRQ/theory-textbook imports, omit `"original_answer_pages"` or set it to `[]` unless the source has discrete answer pages.
- The insertion script renders these pages as full-page screenshots under `data/crops/original_answer_pages/` and stores them on the case for the review-mode "Original answer page" expander.

**Article summary / resume (Scientific articles MRQ only):**
- For `"source": "Scientific articles"` MRQ sessions, add a case-level `"article_summary"` field containing a Markdown summary of the article.
- For all other sources, omit `"article_summary"` or set it to `null` unless explicitly requested.
- The article summary is displayed after the MRQ question expanders in review mode as a collapsed "Article summary" expander.
- The summary must be paraphrased, source-grounded, and clinically useful. Do not paste long source text.
- Use `clinical_vignette` for the article title when importing Scientific Articles, so the MRQ session remains identifiable in the DB.

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
- Short markable answers after the findings step → choose Q3+ free-text targets and assign each to one balance family: `diagnostic_reasoning`, `management`, or `complication_teaching`
This scan must happen before you commit to a question structure — do not fill in the template top-to-bottom without checking what the source offers.

**CORE authenticity rule:** A CORE case should feel like a staged exam case, not a fixed textbook quiz template.
Use a mix of typed and choice-based questions. Findings questions should usually remain `free_text`; this is
the normal CORE anchor for image interpretation. After the findings questions, balance any additional
`free_text` questions across diagnostic reasoning, management, and complication/teaching targets. Diagnosis
and differential questions may be `free_text`, `single_choice`, or `multiple_choice`; choose the format that
best matches the source material and the intended exam step.

1. **Clinical vignette** — one paragraph, ≤ 4 sentences. Patient age/sex, presenting complaint, imaging modality.
   Do NOT reveal the diagnosis.

2. **Questions (4–7):**
   - Q1: "Describe the key findings." `[free_text]` — 3–6 bullet points from the primary modality.
   - Q2: "Describe the key normal and abnormal findings." `[free_text]` — 4–8 bullet points, second modality (if present).
   - Q3: Localising / characterising question `[free_text]` — 1–3 precise statements. OR: "Which of the following are recognised differential diagnoses / causes / features of X?" `[multiple_choice]` — if the source provides a structured differential table or list at this point in the case before the diagnosis is named.
   - Q4: Diagnosis or differential diagnosis. `[single_choice | multiple_choice | free_text]`
     - `free_text`: use when typed recall is more authentic, for example "Give the most likely diagnosis", "Give the two most likely diagnoses", or "List the top 3 differential diagnoses".
     - `single_choice`: use when one best answer with plausible alternatives is a useful exam step. Correct option = textbook diagnosis; 4 plausible differentials as distractors.
     - `multiple_choice`: use when several diagnoses, causes, or features are correct and the source provides or clearly supports a structured list.
     - Do NOT default to any one format. Pick `free_text`, `single_choice`, or `multiple_choice` according to the source answer, the available images, and the sequence of the case. Diagnosis may remain `single_choice` or `multiple_choice` when close mimics make the option set educational.
   - Q5: Management or next step. `[single_choice | multiple_choice | free_text]`
     - `single_choice`: single best next action, 5 options — use when one action clearly precedes all others.
     - `multiple_choice`: "Which of the following are appropriate management steps?" — if multiple actions are correct simultaneously.
     - `free_text`: "Outline the management.", "What would you recommend in the report?", or "What is the next management step?" — if the source gives a short plan, report recommendation, follow-up advice, or next step not reducible to a true best-option item.
   - Q6/Q7 (optional): secondary finding, complication, aetiology, classification, staging, or teaching point. `[single_choice | multiple_choice | free_text]` — add whenever the source provides a structured list or concise markable item that is educationally valuable and not already covered by Q3–Q5.

**Later free-text target selection rule:**
- Q1 and Q2 findings may remain consistently `free_text`; do not count this as undesirable templating.
- Count Q3+ `free_text` questions into one of three target families:
  - `diagnostic_reasoning`: direct diagnosis, differential diagnosis, localisation, classification/staging, or discriminating features.
  - `management`: next step, treatment, report recommendation, or follow-up.
  - `complication_teaching`: complications, pitfalls, associations, epidemiology, or clinical pearls.
- Target 33% per family across a batch, with 30-35% acceptable when the source supports it.
- Direct diagnosis free text is valid and counts as `diagnostic_reasoning`.
- Diagnosis may be `free_text`, `single_choice`, or `multiple_choice` depending on the case.
- If diagnosis stays choice-based, differential diagnosis or discriminating features can still satisfy `diagnostic_reasoning`.
- Do not let management or pitfall questions absorb most conversions just because they are easy to mark.
- For very small batches, use nearest practical rounding but still report percentages.

Useful later free-text stems:
- `Give the most likely diagnosis.`
- `What are the two most likely differential diagnoses?`
- `What would you recommend in the report?`
- `What is the next management step?`
- `What follow-up is appropriate?`
- `Name the most important complications.`
- `What pitfall should be considered?`
- `What classification or stage applies?`

**Later free-text balance validation:**
- Count only Q3+ `free_text` questions. Exclude Q1/Q2 findings from the calculation.
- Assign each to exactly one family: `diagnostic_reasoning`, `management`, or `complication_teaching`.
- Calculate percentages as: `family_count / total_later_free_text_questions * 100`.
- Target: 33% per family.
- Passing range: each family must be 30-35%, unless the source genuinely cannot support it.
- If any family is outside 30-35%, revise the batch before insertion.
- Required validation summary:
```text
Later free-text distribution:
- diagnostic_reasoning: 34%
- management: 32%
- complication_teaching: 34%
Validation: pass
```
- If the source forces an exception, report:
```text
Validation exception:
- failing family:
- observed percentage:
- reason source cannot support target balance:
- affected case numbers:
```

**CORE question-style variation rule:**
- Before drafting a batch of CORE cases, plan the question structure for each case, not only the answer keys.
- Do not use the same fixed Q1-Q5 structure for every case. Vary question count, question stems, and question types according to what the source actually offers.
- Avoid repeated generic stems across a batch, especially repeated "What is the most likely diagnosis?", "Describe the CT findings", and "Which source-supported statements are correct?"
- Findings questions may be consistently free text, but later reasoning questions must vary according to the source.
- Do not make every diagnosis question a choice question, and do not make every diagnosis question free text. Use the format that best matches the case.
- Hard validation before insertion: if Q3+ free-text target families are outside the 30-35% range, revise the question structures before import unless a documented source-based exception applies.
- Hard validation before insertion: if the batch reads as a repeated template, revise the visible question text and case structures before import.

**Image sequencing rule:**
- If a later diagnosis, differential, or management question still depends on earlier images, repeat the relevant `page_images` on that later question.
- Do not leave image-dependent later questions without images only because the images first appeared on Q1 or Q2.
- Answer-page figures and annotated images still belong in `answer.page_images`, not in the question block.
- For staged modality/image-group questions, image assignment is question-specific, not page-wide. If Q1 asks for CT
  findings and Q2 asks for CTA/MRI/US/radiographic/follow-up findings, Q1 receives only the CT images and Q2 receives
  only the CTA/MRI/US/radiographic/follow-up images. Do not attach the entire question-page image set to every
  modality-specific question.
- Staged image groups include CT vs CTA, radiograph vs CT, US vs MRI, CT vs MRI, DSA/angiography vs CT, baseline vs
  follow-up, pre-contrast vs post-contrast, arterial vs venous/delayed phase, and different MR sequences when each
  group supports a distinct interpretive task.
- If the source page contains labelled panels (A, B, C...) or the answer text maps specific findings to panels,
  use that mapping to assign `page_images` to the correct question. If PyMuPDF image order is unclear, visually inspect
  the rendered page before finalising image indices.
- **Hard validation before insertion:** staged modality/image-group questions must not have identical `page_images`
  unless the question text explicitly asks the learner to compare the same images. A modality-specific findings
  question must not have empty `page_images` if the relevant images exist elsewhere in the case. If overlap is needed,
  it must be clinically justified and documented in the validation notes.

3. **Answers:**
   - `free_text`: short noun phrases, one finding per line, no full stop.
   - `single_choice`: `answer_text` = text of correct option; `correct_options` = null.
   - `multiple_choice`: `correct_options` = 0-based indices; `answer_text` = null.
   - Explanation (2–5 sentences): WHY findings → diagnosis, pathophysiology, clinical pearl. Never reference options by letter (a, b, c, d, e) in the explanation — refer to the relevant content instead (e.g. "The claim that X is incorrect because…" not "Option b is incorrect").

4. **Options** (choice questions): always exactly 5, in the `options` array only. Do NOT embed options inside `question_text` — the question stem ends at the question mark.

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

**CORE wording rules:**
- Do not use meta/source wording in visible question stems, such as "source-supported", "according to the source", "model answer", or "which statements are source-supported".
- Prefer exam wording: "Which statements are correct?", "Which features support this diagnosis?", "Which differential diagnoses should be considered?", "What would you recommend?", or "What is the next management step?"
- Do not reveal the final diagnosis in pre-diagnosis stems. Diagnosis names may appear in diagnosis options, answer text, explanations, and post-diagnosis teaching questions.

**Style:** British English clinical register. ST4–ST7 level. Do not invent findings. Multiple source cases → multiple output case objects.

---

## Short Cases Prompt

**Context:** Same as CORE above. Text is authoritative. Images are native embedded figures.

**Chapter assignment:** Same rules as CORE. Skip non-case content silently.

**SHORT CASE FORMAT**

A Short Case (SC) is a focused spotter-style case, similar to an oral/exam short case rather than
a full CORE long case. The emphasis is: image first, localise the abnormality, identify the key
imaging findings, give a short differential, then commit to the most likely diagnosis or one
high-yield management/disease-fact question. Typical length: 3–5 questions.

1. **Clinical vignette / Clinical data** — 1–3 sentences or bullets. Include patient age/sex and the
   relevant presentation/laboratory context. Do NOT name the diagnosis. Mention the modality only if the
   source clinical data or displayed case format makes it explicit; otherwise let the images carry the modality.

2. **Questions:**
   - Q1 — usually image-localisation / hotspot style: "Indicate the abnormality." `[free_text]`
     Answer: one short sentence naming the abnormality and its precise location. If the source case has
     two required clicks/regions, use Q1A and Q1B as separate `free_text` questions or combine them clearly
     in one answer.
   - Q2 — imaging findings: "Which radiological findings do you recognise?" or
     "CT/MRI/US/radiographic findings include..." `[multiple_choice, 5 options]`
     Use source-supported imaging signs. This is often the most important SC question after localisation.
   - Q3 — differential diagnosis: `[multiple_choice | free_text]`
     Use `multiple_choice` when the source provides several plausible differentials. Use `free_text` for
     prompts such as "List the top 2 differential diagnoses" or "Give the top 3 differential diagnoses".
   - Q4 — diagnosis: "What is the most likely diagnosis?" `[single_choice, 5 options]`
     Use the source-stated diagnosis as the correct option. Distractors should be close imaging/clinical
     mimics from the same body system.
   - Q5 (optional) — targeted knowledge, complication, management, or disease-fact question:
     `[multiple_choice | single_choice | free_text]`
     Use this only when the source provides a useful exam-relevant teaching point. Good examples:
     "Regarding this diagnosis, which statements are correct?", "Which complications should be considered?",
     "What is the appropriate next management step?", or "Which associations are recognised?"

   Not every case needs all five questions. Preserve the natural source structure. Some short cases may have
   only Q1, Q3, and Q4 if the source case is sparse or if an intermediate question is absent.

**SC question-style variation rule:**
- Before drafting a batch of short cases, plan the question structure for each case, not only the answer keys.
  The plan should deliberately vary the number of questions, question stems, and question types across the batch.
- Do not use the same fixed 4-question template for every case. A normal batch should contain a mixture of
  3-, 4-, and, where the source supports it, 5-question cases. If every case has exactly the same structure,
  the batch fails validation unless the source is genuinely uniform and sparse.
- Q1 may consistently be a localisation/hotspot question, but Q2-Q5 must vary according to the source. Rotate
  between imaging-feature recognition, top-differential selection, diagnosis, distinguishing-feature questions,
  complication/association questions, and management/next-step questions.
- Avoid repeating the same stem wording across consecutive cases. For example, do not make every Q2
  "Which imaging features support this diagnosis?" and every Q3 "Which statements are source-supported?"
  Acceptable variation includes:
  - "Select the most plausible differentials for this imaging appearance."
  - "Which findings favour the leading diagnosis over its mimics?"
  - "Which entities belong in the top differential?"
  - "Which source-supported teaching points are useful in this case?"
  - "Which complications or associations should be considered?"
  - "What is the single most likely diagnosis?"
- Use `multiple_choice` for top-differential selection when the source provides several named mimics and good
  same-domain distractors. Use `free_text` for top-2/top-3 lists when the ranked list itself is the learning
  target. Use `single_choice` only when one diagnosis or next step is clearly being tested.
- **Hard validation before insertion:** if the batch reads as a repeated template, if nearly every case has the
  same question count, or if the same Q2/Q3 stem family recurs throughout, revise the visible question text and
  case structures before import.

**SC diagnosis-blinding and sequencing rule:**
- If a later question asks for the most likely diagnosis, all earlier question stems must be diagnosis-blinded.
  Do not name the final diagnosis in pre-diagnosis stems. Bad: "Which findings favour renal osteodystrophy?"
  before asking "What is the diagnosis?" Good: "Which imaging findings are demonstrated?" or
  "Which findings help distinguish this pattern from its mimics?"
- Do not use stems such as "Regarding this diagnosis..." or "Which findings support [diagnosis]?" before the
  diagnosis has been revealed. Those are post-diagnosis teaching questions and belong after the diagnosis
  question, or the separate diagnosis question should be omitted.
- If a pre-diagnosis differential question lists named diseases and includes the final diagnosis as one of the
  correct options, do not then ask an obvious single-best diagnosis question immediately afterwards. Either
  ask the single-best diagnosis first, then use a post-diagnosis differential/pearl question; or make the
  differential question the diagnostic question and skip the extra diagnosis item.
- Pre-diagnosis imaging questions should describe the abnormality, localisation, modality findings, pattern,
  and discriminating signs without naming the answer. Final diagnosis names may appear in the diagnosis
  question options, in answer explanations, and in post-diagnosis teaching questions.
- Pre-diagnosis stems must also avoid **semantic leakage**, not just exact diagnosis names. Do not include
  diagnosis-adjacent qualifiers, disease-specific adjectives, mechanism labels, exposure labels, or syndrome
  names that make the answer obvious before the diagnosis question. Bad examples before the diagnosis:
  "Describe the sarcoid-related chest radiographic findings", "Describe the asbestos-related pleural
  findings", "Which findings support acute chest syndrome?", "Describe the bronchiectatic pattern" when
  bronchiectasis is still being tested, or "Describe the postemetic pneumomediastinum pattern" before
  Boerhaave syndrome is asked. Use neutral alternatives such as "Describe the chest radiographic findings",
  "Describe the pleural findings", "Which clinical and imaging findings are demonstrated?", "Describe the
  airway pattern", or "Describe the pneumomediastinum pattern".
- **Hard validation before insertion:** scan every case for answer leakage. If the final diagnosis appears in
  a stem before the diagnosis question, or if a pre-diagnosis stem contains a disease-specific clue that
  effectively gives away the answer, the case fails validation and must be rewritten.

**SC image sequencing rule:**
- Short cases with more than one modality or image group must follow the global SC/CORE image-staging rule.
- Do not put CT + CTA + MRI + radiograph images all on Q1 unless Q1 genuinely asks for all of them.
- If Q1 asks for the initial abnormality and Q2 asks for the second modality or characterising images, split the image refs accordingly.
- Before insertion, verify that every image-dependent SC question has its own relevant images and that no staged questions share identical `page_images` by accident.

3. **Options:** always exactly 5. `single_choice` → `answer_text` = correct option text.
   `multiple_choice` → `answer_text` = null and `correct_options` = 0-based indices. For SC multiple-choice
   questions, use the same correct-answer distribution principles as MRQs when there are multiple SCs in a
   batch: avoid making every question 4-correct, and vary correct positions a–e.
   Choice-question `question_text` must contain the stem only. Do NOT embed labelled options (`a. ...` or
   `1. ...`) inside `question_text`; the app renders choices from the structured `options` array.

**SC multiple-choice answer distribution rule:**
- This applies to every `multiple_choice` question inside Short Cases, including imaging findings,
  differential, complication, risk-factor, association, and teaching-pearl questions.
- Before drafting a batch of short cases, plan the intended number of correct answers and their positions for
  each `multiple_choice` question. Do not write all true statements first and then add one false option at the end.
- Across a batch of short cases, use a fair spread of 1-, 2-, 3-, and 4-correct questions where the source
  supports it. Most SC batches should have many 2- and 3-correct questions, some 4-correct questions, and
  occasional 1-correct questions. Do not make 4-correct or 3-correct questions the default.
- Spread correct answers across positions a–e. Avoid repeated front-loaded patterns such as `[0, 1, 2]` or
  `[0, 1, 2, 3]`. Correct options should appear in later positions (`c`, `d`, `e`) as naturally as in `a` and `b`.
- If a source list naturally contains 3 or 4 true statements, reorder options so the correct answers are not
  clustered at the beginning, and add plausible same-domain distractors in mixed positions.
- Final audit before insertion: count correct-answer lengths and a–e positions for SC `multiple_choice`
  questions in the batch. If the distribution is visibly predictable, revise option order and distractor
  placement before importing.
- **Hard validation before insertion:** count correct-answer lengths and a-e positions for SC
  `multiple_choice` questions in the batch. This is a pass/fail quality gate, not a descriptive report.
  If the distribution is visibly skewed (for example, mostly 3-correct questions, mostly 4-correct
  questions, or one answer position such as `b` appearing far more often than the others), the batch
  **fails validation** and must not be inserted.
- For ~20 SC multiple-choice questions, use this as the normal target unless the source genuinely forces
  a different spread: 1 correct = 2-3 questions; 2 correct = 5-7; 3 correct = 6-8; 4 correct = 3-5.
  For smaller/larger batches, scale this proportionally. No single correct-answer count should dominate
  the batch.
- Rotate between several visibly different SC correct-count profiles rather than reusing the same blueprint
  every batch. Pick the profile before drafting options, then adapt only when the source genuinely cannot
  support it. For ~20 SC multiple-choice questions, acceptable profiles include:
  - Profile A: 1 correct = 2; 2 correct = 6; 3 correct = 7; 4 correct = 5.
  - Profile B: 1 correct = 3; 2 correct = 7; 3 correct = 6; 4 correct = 4.
  - Profile C: 1 correct = 2; 2 correct = 8; 3 correct = 6; 4 correct = 4.
  - Profile D: 1 correct = 3; 2 correct = 5; 3 correct = 8; 4 correct = 4.
  For ~10 SC multiple-choice questions, scale approximately, for example:
  - Mini A: 1 correct = 1; 2 correct = 3; 3 correct = 4; 4 correct = 2.
  - Mini B: 1 correct = 1; 2 correct = 4; 3 correct = 3; 4 correct = 2.
  - Mini C: 1 correct = 2; 2 correct = 3; 3 correct = 3; 4 correct = 2.
  Do not use the same profile in consecutive batches unless the source content forces it.
- Correct-answer positions must also pass validation. Spread correct answers across `a`, `b`, `c`, `d`,
  and `e`; if one position is obviously overrepresented or the batch is front-loaded, revise option order
  and option wording before import.
- Reporting that a batch is "3-correct heavy", "4-correct heavy", "`b`-heavy", or otherwise skewed is
  not acceptable validation. It is a failed validation result. Fix the visible option text, the `options`
  array, `correct_options`, and the explanation before insertion.

**Distractor quality rule:**
- Incorrect options must be plausible, same-domain alternatives, not random unrelated items.
- Prefer distractors that are clinically or radiologically adjacent to the topic but clearly unsupported by the source.
- For management questions, wrong options should be plausible but inappropriate next steps.
- For risk-factor, complication, classification, or feature-list questions, wrong options should come from the same clinical category but must not be listed or implied by the source.
- Avoid silly or obviously unrelated distractors unless the source topic genuinely offers no reasonable alternatives.
- Do not use a distractor that is true from general medical knowledge if it would make the question ambiguous but is not supported by the source.

4. **Explanation** (1–4 sentences): imaging features supporting diagnosis; why main distractors are excluded. Never reference options by letter — refer to the relevant content instead (e.g. "The claim that X is incorrect because…" not "Option b is incorrect").

**Anti-hallucination rules:** identical to CORE above. Q2/Q3 may be omitted if the source case is too brief
to support them — do not invent questions. Q1 is non-negotiable unless the source case genuinely starts with
a findings/differential question and no localisation task is present.

**Image handling:** Attach the relevant case images to the question where they are first needed. For
screenshot-based short cases where images appear in order across multiple screenshots, preserve that order and
use the surrounding screenshots to understand context before writing the case. Do not treat each screenshot as
a separate case unless the on-screen case identifier or question sequence changes.

**Style:** British English. Each SC should be solvable quickly as a spotter-style case. Do not invent findings.
Multiple source cases → multiple output objects.

---

## MRQ Prompt

**Context:** You are a radiology education expert specialising in the EDiR exam. You are reading a radiology
theory/textbook chapter directly. The extracted text is your only authoritative source.

**Chapter assignment:** Assign the generated MRQ cluster to the single most appropriate DB chapter based on
its topic. If a section of text is front matter, an index, or non-educational prose, skip it silently.

**MRQ FORMAT RULES**

Each MRQ is a standalone multiple-select question — no shared clinical vignette.
Group the chapter content by topic; generate one cluster of related MRQs per topic.
Scale to content volume: ~2–3 questions per page of meaningful theory text for most textbook batches, with up to ~30 questions per ~12-page batch when the source is dense enough (e.g. BI-RADS, protocols, classifications, structured differentials, staging, modality-specific feature lists). Skip or reduce for image-only or sparse pages. Never pad to hit a target — generate fewer if the source is thin.

1. **Question body** — one of:
   - Template A (image-based): "<Brief clinical context>.\n\nWhich of the following statements are correct regarding this image?"
   - Template B (knowledge): "Regarding <topic>, which of the following statements are correct?"

2. **Options** — always exactly 5, in the `options` array only. Do NOT embed options inside `question_text` — the question stem ends at the question mark.
   1–4 correct answers per question. Never all-correct or none-correct.
   Distractors must be plausible and at the same specificity level as the correct answers.
   Across a batch, deliberately vary the number of correct answers. Use a non-predictable mix of
   1, 2, 3, and 4 correct options; do not default to 4 correct answers. As a rough target, no single
   correct-answer count should dominate the batch unless the source genuinely forces it.
   These distribution targets apply to **all MRQ sources**, not only Core Radiology:
   - For ~15 questions, aim for roughly: 1 correct = 1-2 questions; 2 correct = 4-5; 3 correct = 5-6;
     4 correct = 3-4.
   - For ~20 questions, aim for roughly: 1 correct = 2-3 questions; 2 correct = 5-6; 3 correct = 7-8;
     4 correct = 3-5.
   - For ~30 questions, rotate between several noticeably different fair profiles rather than repeating the
     same blueprint every batch. Acceptable examples:
     - Profile A — balanced middle: 1 correct = 4; 2 correct = 9; 3 correct = 11; 4 correct = 6.
     - Profile B — 2-correct heavy: 1 correct = 5; 2 correct = 12; 3 correct = 8; 4 correct = 5.
     - Profile C — 3-correct heavy: 1 correct = 3; 2 correct = 8; 3 correct = 13; 4 correct = 6.
     - Profile D — higher 4-correct, still controlled: 1 correct = 4; 2 correct = 8; 3 correct = 10; 4 correct = 8.
     Do not use the same profile in consecutive batches unless the source genuinely forces it. Use the
     profile that best fits the source, but do not let 4-correct questions become the default.
   - If the batch has >=10 questions, it should normally include at least one 1-correct question and at
     least two 2-correct questions.
   - 4-correct questions are allowed, but they should be a minority rather than the default.
   **Correct-answer position distribution:** Spread correct answers across all five positions (a–e) — do not draft correct statements first and distractors last, as this creates a detectable a > b > c > d > e frequency gradient that makes the test gameable. Aim for each position to be correct in roughly 40–65% of questions across a batch. Deliberately assign correct options to positions c, d, and e as often as to a and b.
   **Blueprint checkpoint:** Before generating any MRQ batch, write a compact working-note blueprint showing
   the planned answer-count and rough answer positions for every question. This applies to all MRQ sources,
   not only Core Radiology. Example: `Q01 4 correct: b/c/d/e; Q02 2 correct: a/d; Q03 3 correct: b/d/e;
   Q04 1 correct: c`. Do not start drafting the actual options until this blueprint exists. If the source
   cannot support the assigned count for a topic, change the blueprint before writing that question.

3. **Correct options** — 0-based indices, e.g. `[0, 2, 4]` for a, c, e.

4. **Explanation** — 3–6 sentences: why each correct option is right, why the main distractor is wrong, clinical/imaging pearl. Never reference options by letter (a, b, c, d, e) — refer to the relevant content instead (e.g. "The claim that X is incorrect because…" not "Option b is incorrect").

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
- Set case-level `original_answer_pages` to every answer/discussion page for that case, from the first answer heading through the end of the case answer before the next case or packet/backmatter.

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

---

## Book-Specific Tips: Crack the Core (`Crack the CORE exam Volumul 1.pdf`, `Crack the CORE exam Volumul 2.pdf`)

### Source label
- Insert all MRQs from these books with `"source": "Crack the Core"`.
- Do not create separate source labels for different volumes; Volume 1 and Volume 2 belong under the same app source.
- Use `"section": "mrq"` only. Do not generate CORE or SC cases from this book.

### Working files
- Put DB backups, temporary JSON files, scratch extraction files, and validation scratch files in:
  `C:\Users\Razvan\Documents\Radiologie\backups`
- Keep only durable project references (such as this prompt file) in the repo unless the user asks otherwise.

### Book structure
- This is a high-yield review/theory book written in an informal, sarcastic style. The medical content is useful; the rhetorical style is not the target output.
- These PDFs have no reliable bookmarks. Use the printed index, OCR text, and direct page inspection.
- Skip front matter, legal pages, motivational prose, resource lists, non-medical jokes, and non-radiology filler.
- Volume 1: skip the introductory "Art of War" / study strategy chapter; the first substantive radiology chapter is Thoracic.
- Volume 2: the first substantive radiology chapter is Musculoskeletal; skip the final Strategy chapter by default unless explicitly requested.

### Volume 1 printed page to PDF page mapping
- The printed index gives chapter ranges in printed page numbers.
- For Volume 1, use:
  - `1-based PDF page = printed page - 1`
  - `0-based PDF page = printed page - 2`
- Some chapter starts include title/divider/blank pages. Inspect the start of each range and skip pages without usable medical content.

### Volume 1 chapter mapping

| Book chapter | Printed pp | 1-based PDF pp | 0-based PDF pp | DB chapter |
|--------------|------------|----------------|----------------|------------|
| Ch 1 Art of War | 9-41 | 8-40 | 7-39 | Skip |
| Ch 2 Thoracic | 43-113 | 42-112 | 41-111 | Chest and Thorax Radiology (id=4) |
| Ch 3 Cardiac | 115-149 | 114-148 | 113-147 | Cardiac Radiology (id=3) |
| Ch 4 Pediatrics | 151-260 | 150-259 | 149-258 | Pediatric Radiology (id=10) |
| Ch 5 GI | 261-350 | 260-349 | 259-348 | Abdominal Radiology (id=1) |
| Ch 6 Urinary | 353-399 | 352-398 | 351-397 | Genitourinary Radiology (id=5) |
| Ch 7 Reproductive | 401-469 | 400-468 | 399-467 | Genitourinary Radiology (id=5) |
| Ch 8 Endocrine | 471-488 | 470-487 | 469-486 | Split by topic |
| Ch 9 Nukes | 491-570 | 490-569 | 489-568 | Hybrid Imaging (id=14) |

### Endocrine routing
- Do not force the Endocrine chapter into a single DB chapter blindly.
- Adrenal content -> Genitourinary Radiology (id=5) unless explicitly paediatric.
- Thyroid/parathyroid/neck endocrine content -> Head and Neck (id=6).
- Paediatric adrenal/endocrine content -> Pediatric Radiology (id=10) when the topic is explicitly paediatric-focused.
- If a batch mixes adrenal and thyroid heavily, split it by topic before import.

### Volume 2 chapter mapping
- The Volume 2 PDF has no reliable bookmarks. The TOC is on page 3 of the PDF viewer, with the usable printed index on the following contents page.
- For Volume 2 numbered content pages, the printed page number usually equals the 0-based PDF page index:
  - `0-based PDF page = printed page`
  - `1-based PDF page = printed page + 1`
- Chapter starts often include a title/divider page; inspect the first page of each range and skip divider/blank pages before generating questions.

| Book chapter | Printed pp | 1-based PDF pp | 0-based PDF pp | DB chapter |
|--------------|------------|----------------|----------------|------------|
| Musculoskeletal | 9-127 | 10-128 | 9-127 | Musculoskeletal Radiology (id=8) |
| Neuroradiology | 129-299 | 130-300 | 129-299 | Neuroradiology (id=9) |
| Vascular | 301-346 | 302-347 | 301-346 | Interventional and Vascular Radiology (id=7) |
| Interventional | 347-448 | 348-449 | 347-448 | Interventional and Vascular Radiology (id=7) |
| Mammo | 451-521 | 452-522 | 451-521 | Breast Radiology (id=2) |
| Strategy | 523-585 | 524-586 | 523-585 | Skip by default |

### Strategy chapter routing
- Skip the Volume 2 Strategy chapter by default. It is primarily exam technique, motivation, and test-taking workflow rather than radiology content.
- Do not map Strategy to Communication and Management unless the user explicitly asks for non-interpretive / exam-strategy MRQs.

### Tone and content filtering
- Extract the medical/radiological fact, differential, sign, association, staging point, anatomy rule, management pearl, or exam trap.
- Rewrite final stems, options, and explanations in neutral British clinical register.
- Do not include profanity, insults, demographic stereotypes, irrelevant jokes, pop-culture jokes, or motivational rhetoric.
- Preserve useful "original flavour" only when it functions as a clean memory aid. The mnemonic may be retained or lightly rewritten if it helps recall an imaging/anatomy/pathology association and does not introduce offensive wording.
- If a useful fact is embedded inside a joke, keep the fact and discard the joke.
- Do not preserve offensive/race/body-habit/stereotype mnemonics. Convert only the underlying source-supported medical association into neutral wording.

### High-yield MRQ targets
- Prioritise sections explicitly framed as:
  - `THIS vs THAT`
  - "classic scenario"
  - "buzzword"
  - "Aunt Minnie"
  - "high yield trivia"
  - "top things"
  - named signs
  - differential lists
  - anatomy localisation rules
  - staging, complications, and management pearls
- The book is built for multiple-choice exam preparation, so many passages naturally support MRQs. Still avoid low-value recall if the point cannot be used for image interpretation, diagnosis, protocol choice, staging, complication recognition, or management.
- Use source-grounded distractors from adjacent same-chapter topics, especially `THIS vs THAT` comparisons. Do not import outside radiology facts just to make a distractor.

### Image handling
- This PDF is OCR over full-page scans. PyMuPDF typically exposes one large full-page image object per page (~1240 x 1650 px), not separate clean clinical figure crops.
- Default to **text-only MRQs** with empty `page_images` and `answer.page_images`.
- Do not attach full-page scans as images: they include surrounding textbook text, jokes, and potential answer leakage.
- If image-based MRQs are later required, build a separate manual crop/render workflow first. Do not use the normal `page_images` extraction path for this book.

### Batching
- Process within the printed chapter ranges above, usually in ~10-12 OCR pages per batch.
- Aim for up to ~30 MRQs per batch when the OCR pages are dense enough with usable medical content, especially `THIS vs THAT`, differential, staging, anatomy, or named-sign sections. Do not pad to reach 30; generate fewer questions when the pages are sparse, repetitive, noisy, or mostly humour/non-medical prose.
- Each batch = one case object / one MRQ session.
- Insert each completed batch under the mapped DB chapter and `"source": "Crack the Core"`.
- Before drafting each batch, produce the global MRQ blueprint: intended correct-answer count and rough answer positions for every planned question.
- Rotate the ~30-question MRQ distribution profile between batches when possible (e.g. A, B, C, D from the general MRQ rules) so the learner does not see the same answer-count pattern every session.
- Run the usual final audit before insertion: option count, correct-answer count distribution, answer-position distribution, no all-correct/none-correct, no unselected source-true statements, and no jokes/profanity/stereotypes in final output.

---

## Book-Specific Tips: Crack the Core Case Companion (`Crack the core exam case companion (2015).pdf`)

### Source and section
- Use this book to create **Short Cases** only: `"section": "sc"`.
- Insert all cases with `"source": "Crack the Core - Case companion"`.
- One source book case = one app short case. Do not merge multiple book cases into one app case.
- Rewrite the book's US-style MCQ cases into EDiR-style image-led short cases. Do not import the original stems, jokes, or option wording verbatim unless the wording is already clean and educational.

### Book structure
- The PDF has a usable bookmark/TOC structure and three case-based sections:
  - `Aunt Minnie`: cases 1-125, diagnosis-led image cases.
  - `This vs That`: cases 1-60, paired-comparison / discriminating-feature cases.
  - `Anatomy Quiz`: cases 1-30, labelled anatomy and image-identification cases.
- Skip front matter, copyright pages, divider/title pages, index pages, non-medical jokes, profanity-only material, motivational rhetoric, and non-educational filler.
- Many cases follow a two-page structure:
  - Page 1: source question page with the real clinical image(s) and original MCQ-style prompts. Treat this as the question-side source.
  - Page 2: source answer page with diagnosis, answers, teaching text, and sometimes annotated/repeat images. Treat this as answer-side source; its images usually belong in answer `page_images` only.
- Set case-level `original_answer_pages` to the source answer page, and include any immediately following page only if it is clearly part of the same case answer/teaching section.
- Use both pages as source material before drafting the app case, but keep question-side content diagnosis-blinded.
- Some early pages have mojibake / corrupt text extraction. If text extraction is garbled, use OCR and visual inspection; do not generate case content from unreadable extracted text alone.

### Chapter routing
- Decide the DB chapter per case from the anatomy, modality, and diagnosis. Do not route only from the book section heading.
- Default routing:
  - Intracranial and spine cases -> Neuroradiology.
  - Skull base, sinonasal, temporal bone, orbit, and neck cases -> Head and Neck.
  - Musculoskeletal cases -> Musculoskeletal Radiology.
  - Thoracic lung/pleura/mediastinum cases -> Chest and Thorax Radiology.
  - Cardiac cases -> Cardiac Radiology.
  - Gastrointestinal/hepatobiliary cases -> Abdominal Radiology.
  - Genitourinary, gynaecologic, prostate, and reproductive imaging cases -> Genitourinary Radiology unless clearly fetal/paediatric.
  - Fetal and paediatric congenital cases -> Pediatric Radiology when the paediatric/fetal context is the main tested point.
  - Nuclear medicine / whole-body tracer cases -> Hybrid Imaging.
  - Breast cases -> Breast Radiology.
  - Vascular and interventional cases -> Interventional and Vascular Radiology.
  - Imaging physics, artefact, and technique cases -> Physics, Principles of Imaging Techniques, and Informatics.
- Use `"chapter_match": "exact"` when the case clearly belongs to the selected EDiR chapter; use `"close"` only for pragmatic nearest-fit routing.

### Case conversion rules
- **Aunt Minnie cases:** preserve the spot-diagnosis logic. Typical structure:
  1. Clinical vignette from the book's presentation/history, cleaned and diagnosis-blinded.
  2. Q1 localisation / abnormality recognition, usually `"Indicate the abnormality."` `[free_text]`, with question-page clinical image(s).
  3. Q2 imaging findings or discriminating signs `[multiple_choice | free_text]`.
  4. Q3/Q4 diagnosis or differential diagnosis `[single_choice | multiple_choice | free_text]`, depending on what the source supports.
  5. Optional Q5 targeted teaching pearl, association, complication, management step, or classic history.
- **This vs That cases:** convert to comparison short cases. Preserve the educational target of telling similar entities apart. Use paired-image identification when appropriate, then ask for discriminating signs, pitfalls, or a concise differential. Do not force a separate diagnosis question if the case is primarily a comparison exercise.
- **Anatomy Quiz cases:** convert to anatomy spotter short cases. Use labelled structure identification and one applied anatomy/radiology consequence question when supported. Do not force a disease diagnosis question for pure anatomy cases.
- **Physics / artefact cases:** test artefact recognition, cause, and practical correction. Avoid low-value number memorisation unless the number directly affects imaging interpretation or protocol choice.
- Not every case needs the same number of questions. Use the general Short Case rules: 3-5 questions according to source density, with deliberate variation in Q2/Q3 stem style and question type across each 10-case batch.

### Clinical vignette generation
- The book often provides little or no formal clinical history. Create a short diagnosis-blinded vignette for every app case.
- Use age, sex, symptom, history, risk factor, and modality only when stated on the source question page or answer page.
- The answer page may be used for clinical context only when it explicitly states the context and using it does not reveal the diagnosis.
- If the source gives only a minimal prompt such as "headache", "stuffy nose", or "chest pain", keep the vignette equally minimal, e.g. "A patient presents with headache. Imaging is provided."
- If no clinical context is stated, use a neutral vignette such as "A patient undergoes imaging. Review the provided image(s)."
- Do not invent demographics, symptom duration, laboratory results, operative history, risk factors, modality, or management context unless they are stated or directly visible in the source material.

### Tone and content filtering
- Rewrite final stems, options, and explanations in neutral British clinical register.
- Strip profanity, insults, demographic stereotypes, irrelevant jokes, pop-culture jokes, and motivational rhetoric from final output.
- Preserve a mnemonic only if it is clean, clinically acceptable, and useful for remembering a radiology association or discriminating feature.
- If a useful imaging fact is embedded inside a joke, keep the fact and discard the joke.
- Do not include offensive or unserious distractors from the source; replace them with plausible same-domain distractors grounded in the source case, nearby cases, or the same section.

### Image handling
- This book is image-led. Do **not** apply the text-only image rule used for the Crack the Core MRQ volumes.
- Include all relevant clinical images from the source question page in the relevant question `page_images`.
- Include answer-page clinical, annotated, repeat, or teaching images in `answer.page_images` only, unless the answer image is the only non-revealing clinical image available.
- Do not attach full-page scans, decorative artwork, title/divider images, or answer-leaking composites to question `page_images`.
- If PyMuPDF exposes one large composite or full-page image, visually inspect it before deciding whether it is a usable clinical image, an answer-leaking image, or a page scan to omit.
- If one case contains multiple modalities or clearly separate image groups, stage them across questions using the general SC multi-modality image-staging rule.

### Validation before insertion
- Process in 10-case batches where possible. Each batch must pass validation before insertion.
- Validate sequential `q_number`s and coherent 3-5 question structure for each case.
- Validate no diagnosis leakage in pre-diagnosis stems, except diagnosis names appearing as options in a properly placed differential/diagnosis question.
- Validate that question-side images are relevant and do not leak answer-page labels or explanations.
- Validate exactly 5 options for every `single_choice` and `multiple_choice` question.
- Validate that `question_text` contains only the stem for choice questions; labelled options must live only
  in the structured `options` array.
- Validate `single_choice.answer_text` exactly matches one option.
- Validate every `multiple_choice.correct_options` list has 1-4 correct options.
- Apply the existing SC multiple-choice distribution rules across the batch: fair spread of correct-answer counts and a-e positions. A skewed distribution is a failed validation, not a reportable caveat.
- Validate explanations are source-grounded, concise, clinically useful, and cleaned of jokes/profanity/stereotypes.

---

## Book-Specific Tips: Cases in Radiology (Oxford case-review series)

### Source and sections
- Use this workflow for Oxford `Cases in Radiology` case books, including but not limited to `Body MRI Cases`.
- Insert all cases with `"source": "Cases in Radiology (Oxford)"`.
- Use `"section": "sc"` for Short Cases and `"section": "core"` for CORE-style cases.
- One source case = one app case. Do not create both an SC and a CORE case from the same source case.
- Oxford `Cases in Radiology` inherits all general **Short Cases Prompt** and **CORE Cases Prompt** rules above. This section only adds Oxford-specific source handling, chapter routing, and format-selection rules.

### Book structure
- These books are image-led case books, not theory textbooks. Most cases follow a regular two-page structure:
  - Page 1: case number, `History`, and question-side clinical images.
  - Page 2: answer-page case title containing the diagnosis, followed by `Findings`, `Differential diagnosis`, `Teaching points`, `Management`, and `Further reading`.
- Use the `History` section on the first page as the clinical vignette. Do not invent demographics, symptoms, laboratory data, operative history, risk factors, or modality context.
- The diagnosis is taken from the answer-page case title. Use it as ground truth for the diagnosis answer, but do not leak it into pre-diagnosis stems.
- Ignore `Further reading` as educational content. Use it only as a boundary marker for the end of the case answer if needed.
- Set case-level `original_answer_pages` to the full Oxford answer page for each case, usually the page immediately after the history/image page.
- Skip covers, title pages, contributors, abbreviations, contents, indexes, topic indexes, watermarks, and non-case pages.
- Use bookmarks when present. Verify the page pattern for each Oxford volume before processing; do not assume the exact page offset from another volume without checking.

### Chapter routing
- Decide chapter per case by the primary imaging target, using the book title only as a default for single-subspecialty Oxford volumes.
- Abdominal/hepatobiliary/pancreas/spleen/bowel/peritoneum -> `Abdominal Radiology`.
- Kidney, adrenal, bladder, prostate, urethra, and gynaecologic pelvis -> `Genitourinary Radiology`.
- Heart, valves, myocardium, pericardium, and cardiac masses -> `Cardiac Radiology`.
- Aorta, vascular syndromes, AVM, FMD, venous obstruction, aneurysm, dissection, and endovascular planning -> `Interventional and Vascular Radiology`.
- MR artefacts, coil positioning, SNR, RF coil selection, sequence physics, and general MR technique -> `Physics, Principles of Imaging Techniques, and Informatics`.
- Contrast safety, NSF, and contrast-related risk/management -> `Safety in Radiology`.
- Paediatric routing only when the case is primarily paediatric rather than adult-style body imaging.
- If a case crosses systems, route by the main imaging task being tested, not merely by every organ mentioned in the diagnosis.

### Mandatory pre-drafting scan
Before deciding the app format or writing questions, read the full source case and explicitly consider every available section:
- History
- Question-side image captions / sequence labels
- Answer-page case title
- Findings
- Differential diagnosis
- Teaching points
- Management

Findings and differential diagnosis remain the main focus, but Teaching Points and Management must not be ignored. Use them as one or more of:
- a dedicated question,
- a post-diagnosis teaching or management question,
- answer explanation content,
- a source-grounded distractor pool.

If a section is absent, redundant, or too low-yield to test, it may be skipped, but do not skip sections by habit.

### SC versus CORE selection
- Process in 10-case batches whenever possible.
- Use source-driven format selection, but the default target for a full 10-case Oxford batch is about
  **6 Short Cases and 4 CORE cases**.
- A **5 SC / 5 CORE** mix is acceptable when the source cases are dense enough to justify more long-case
  style testing.
- A **7 SC / 3 CORE** mix is acceptable when the batch is mostly focused spotter-style cases.
- Avoid CORE-heavy batches (> 5 CORE cases per 10) unless the batch genuinely contains unusually dense
  cases with multiple modalities, rich differential diagnosis, management, classification, complications,
  artefact physics, vascular planning, or important teaching points.
- Do not force CORE format just to meet a quota. Do not force SC format by discarding useful source
  material. Format choice remains source-driven, but the batch should normally lean slightly toward
  Short Cases.
- Before drafting each Oxford batch, record the planned SC/CORE mix. If the final mix differs
  substantially from 6 SC / 4 CORE or 5 SC / 5 CORE, the reason must be clear from source density.
- If the final batch has fewer than 10 cases, scale the CORE minimum proportionally and use source density to avoid padding.

Use `sc` when the source case is a focused spotter:
- one main modality or one simple image set,
- a clear abnormality and diagnosis,
- limited teaching points,
- no substantial management/classification/pitfall material beyond one teaching point.

Use `core` when the source case is dense:
- multiple modalities, phases, planes, sequences, or image groups,
- rich differential diagnosis requiring discrimination,
- useful Teaching Points beyond the diagnosis,
- management, prognosis, complication, staging, classification, artefact physics, vascular planning, or protocol logic worth testing.

### Oxford Short Case conversion
- Follow the general Short Cases Prompt exactly: **3-5 questions**, image-led, diagnosis-blinded before diagnosis, varied stems, no options in `question_text`, and balanced SC multiple-choice answer counts and positions.
- A typical Oxford SC should include:
  1. clinical vignette from `History`,
  2. localisation or key abnormality question using question-page image(s),
  3. imaging feature or differential question,
  4. diagnosis question, unless the differential question already functions as the diagnostic question,
  5. optional post-diagnosis teaching or management question.
- Do not convert every Oxford SC into the same four questions. The source sections determine which question types are useful.
- Before drafting a 10-case Oxford batch, assign a planned question count for each SC case. A normal
  batch should visibly mix 3-, 4-, and where supported 5-question SCs. If all or nearly all SC cases have
  four questions, the batch fails validation unless the source is genuinely uniform and sparse.
- Use 3 questions for focused spotters with limited teaching material; use 4 questions for ordinary short
  cases; use 5 questions only when the source provides a worthwhile teaching, management, differential, or
  artefact/protocol target that does not duplicate the diagnosis/finding questions.

### Oxford CORE conversion
- Follow the general CORE Cases Prompt exactly, but for Oxford keep CORE cases to **4-6 questions**
  rather than the generic 4-7 range. Use long-case style, no diagnosis leakage, structured use of free-text /
  single-choice / multiple-choice, plausible same-domain distractors, answer formatting exactly as specified
  above, and no unsupported facts.
- An Oxford CORE case should deliberately test more of the answer page than an SC case. It should normally include:
  - Q1/Q2: key imaging findings, staged by modality, sequence, phase, plane, or image group when appropriate.
  - Diagnosis or differential question using the source diagnosis title and Differential Diagnosis section.
  - At least two source-supported teaching targets from Teaching Points, Management, complications, prognosis, anatomy, classification, artefact physics, or protocol logic.
- For Oxford CORE cases, review all question-page and answer-page images before drafting the imaging
  questions. If the case contains different modalities, sequences, phases, planes, or clearly separate image
  groups, split them into separate imaging questions instead of merging them into one generic findings
  question. Examples: T1 vs T2, in-phase vs opposed-phase, pre-contrast vs post-contrast, arterial vs venous
  or delayed phase, MRCP vs axial MRI, MRI vs CT/radiograph/ultrasound, baseline vs follow-up, or overview
  vs problem-solving images.
- For Oxford CORE and SC cases with staged images, write the image map before the questions. Oxford pages
  often contain several panels on the same page, and PyMuPDF image order may not match the reading order.
  Use captions, panel labels, rendered-page inspection, and the answer text to decide which images belong to
  Q1, Q2, and any later image-dependent question.
- Each staged imaging question should receive only the relevant `page_images` for that modality/image
  group. The corresponding answer-side clinical or annotated images for that modality/image group should
  go in that question's `answer.page_images`.
- A staged Oxford case fails validation if an initial CT/radiograph/MRI question contains the later CTA/
  follow-up/problem-solving images, or if the later CTA/follow-up/problem-solving question has no images
  while those images are present elsewhere in the case.
- Combine modalities/sequences into one findings question only when the source is sparse, when the additional
  image group simply repeats the same finding without adding a separate interpretive task, or when splitting
  would force padding beyond source support.
- Keep diagnosis-blinding intact when staging images: do not attach labelled or answer-revealing answer-page
  images to pre-diagnosis question images.
- Named-diagnosis facts belong after the diagnosis question unless the diagnosis question is omitted because the case is primarily a differential/mapping exercise.
- Before drafting a 10-case Oxford batch, assign a planned question count for each CORE case. A normal
  batch should not cluster every CORE case at the same length; mix 4-, 5-, and 6-question CORE cases
  according to source density.
- Use 4 questions for compact CORE-style cases, 5 questions for standard dense cases, and 6 questions only
  when the answer page contains several distinct high-yield targets. Do not pad beyond source support.

### Image handling
- Question-page clinical images go into question `page_images`.
- Answer-page labelled, repeat, explanatory, or teaching images go into answer `page_images`.
- Include all relevant clinical images from the relevant page; never select only a representative subset.
- Do not attach answer-page labelled images to pre-diagnosis question images if they reveal the diagnosis or answer.
- Do not rigidly apply the >=200 px rule for this series. Some Oxford answer-page images are small but clinically relevant; visually inspect before omitting small images.
- If one source case has multiple modalities, sequences, phases, planes, or clearly separate image groups, stage them across questions using the general SC/CORE multi-modality rules.
- For Oxford, do not treat the history/question page as one undifferentiated image pool. If a case has
  separate CT and CTA panels, radiograph and CT panels, ultrasound and MRI panels, or baseline and follow-up
  panels, split those panels across the corresponding questions unless one stem explicitly asks for a
  combined comparison.
- If PyMuPDF exposes a full-page scan, watermark, logo, or decorative non-clinical object, visually inspect before deciding whether to omit it.

### Validation before insertion
- Validate each 10-case batch before insertion.
- Confirm every source case has exactly one output case and that the batch has at least 3 CORE cases when it contains 10 cases.
- Validate all usual SC/CORE requirements: sequential `q_number`s, **3-5 SC questions**, **4-6 Oxford
  CORE questions**, no pre-diagnosis leakage, no options inside `question_text`, exactly 5 options for choice
  questions, single-choice answer text present in options, and multiple-choice `correct_options` length 1-4.
- Validate **semantic diagnosis blinding** explicitly. Before the diagnosis question, imaging stems must be
  generic only. Use stems such as:
  - "Describe the imaging findings."
  - "Describe the MRI findings."
  - "Describe the MRCP findings."
  - "Describe the CT findings."
  - "Indicate the abnormality."
  Do not include anatomical localisation, organ/system labels, vessel names, compartment labels,
  pathology-class labels, mechanism labels, artefact mechanism labels, or pattern labels before the diagnosis
  is asked. These details belong in the answer, explanation, post-diagnosis teaching questions, or diagnosis
  options, not in a pre-diagnosis stem. If a pre-diagnosis stem is more specific than the modality or
  "abnormality", rewrite it before insertion.
- Validate planned question-count variation across the batch. If SCs are all/nearly all 4-question cases, or
  CORE cases all/nearly all have the same number of questions, the batch fails validation and must be revised
  before insertion.
- Validate `multiple_choice` questions separately from `single_choice` questions. Do not count `single_choice`
  diagnosis questions as "1-correct MCQs" when judging correct-answer distribution; that hides imbalance.
- For Oxford SC/CORE batches, the correct-count audit is pass/fail on **multiple_choice only**:
  - Count only questions where `q_type == "multiple_choice"`.
  - Report the distribution of 1-, 2-, 3-, and 4-correct MCQs.
  - A batch fails validation if 3-correct or 4-correct questions dominate, if there are no 1-correct MCQs
    when the batch has enough MCQs to support at least one, or if 2-correct MCQs are underrepresented.
  - Do not insert a batch merely because the combined choice-question distribution looks balanced after
    `single_choice` questions are included.
- Apply the existing SC multiple-choice distribution and a-e position rules to SC questions in the batch.
- Apply the same balanced multiple-choice principles to CORE multiple-choice questions; avoid predictable
  all-true or front-loaded answer patterns.
- Validate correct-answer positions on **multiple_choice only** as well as across all choice questions. The
  multiple-choice position spread must not be front-loaded; `d` and `e` should appear naturally, not as rare
  distractor-only positions.
- Validate that each case considered Findings, Differential Diagnosis, Teaching Points, and Management, and that clinically useful content from those sections appears in the questions or explanations.
- Store backup DB copies and temporary JSON/extraction files only under `C:\Users\Razvan\Documents\Radiologie\backups`.

---

## Book-Specific Tips: RadCases (Thieme case-review series)

### Source and sections
- Use this workflow for Thieme RadCases case books.
- Insert all cases with `"source": "Radcases"`.
- Use `"section": "sc"` for Short Cases and `"section": "core"` for CORE-style cases.
- One source case = one app case. Do not create both an SC and a CORE case from the same source case.
- RadCases inherits all general **Short Cases Prompt** and **CORE Cases Prompt** rules above. This section only adds RadCases-specific source handling and format-selection rules.

### Book structure
- RadCases books are case books, not theory textbooks. Most cases follow a reliable two-page structure:
  - Page 1: case number, clinical presentation, and question-side clinical images.
  - Page 2: differential diagnosis, figure caption / imaging findings, essential facts, other imaging findings, pearls and pitfalls, and answer-side clinical or labelled images.
- Set case-level `original_answer_pages` to the RadCases answer page for each case, usually the page immediately after the question/image page.
- Skip covers, title pages, prefaces, further readings, indexes, watermarks, and non-case pages.
- Use bookmarks when present. In the sampled `RadCases Cardiac Imaging` PDF there are 100 cases and the bookmarks map cleanly to every case.
- For the sampled cardiac PDF only, the page pattern can be used as a check: case `N` question page is viewer page `10 + 2N`; the answer page is the next viewer page. Always verify this before a new RadCases volume.

### Chapter routing
- Decide chapter per case, but use the book title as the default chapter for single-subspecialty RadCases volumes.
- `RadCases Cardiac Imaging` defaults to `Cardiac Radiology` with `"chapter_match": "exact"`.
- Future RadCases volumes should default by title, for example chest -> Chest and Thorax, GU -> Genitourinary, MSK -> Musculoskeletal, paediatric -> Pediatric, and so on.
- Override per case only when the case clearly belongs elsewhere, such as a vascular/interventional procedure, hybrid imaging tracer case, or head-and-neck case inside a mixed volume.

### Mandatory pre-drafting scan
Before deciding the app format or writing questions, read the full source case and explicitly consider every available section:
- Clinical Presentation
- Differential Diagnosis
- Imaging Findings / figure caption
- Essential Facts
- Other Imaging Findings
- Pearls & Pitfalls

Imaging findings and differential diagnosis remain the main focus, but Essential Facts, Other Imaging Findings, and Pearls/Pitfalls must not be ignored. Use them as one or more of:
- a dedicated question,
- a post-diagnosis teaching or pitfall question,
- answer explanation content,
- a source-grounded distractor pool.

If a section is absent, redundant, or too low-yield to test, it may be skipped, but do not skip sections by habit.

### SC versus CORE selection
- Process in 10-case batches whenever possible.
- Use source-driven format selection, but the default target for a full 10-case RadCases batch is about
  **6 Short Cases and 4 CORE cases**.
- A **5 SC / 5 CORE** mix is acceptable when the source cases are dense enough to justify more long-case
  style testing.
- A **7 SC / 3 CORE** mix is acceptable when the batch is mostly focused spotter-style cases.
- Avoid CORE-heavy batches (> 5 CORE cases per 10) unless the batch genuinely contains unusually dense
  cases with multiple modalities, rich differential diagnosis, management, classification, complications,
  or important pearls/pitfalls.
- Do not force CORE format just to meet a quota. Do not force SC format by discarding useful source
  material. Format choice remains source-driven, but the batch should normally lean slightly toward
  Short Cases.
- Before drafting each RadCases batch, record the planned SC/CORE mix. If the final mix differs
  substantially from 6 SC / 4 CORE or 5 SC / 5 CORE, the reason must be clear from source density.
- If the final batch has fewer than 10 cases, scale the CORE minimum proportionally and use source density to avoid padding.

Use `sc` when the source case is a focused spotter:
- one main modality or one simple image set,
- a clear abnormality and diagnosis,
- limited essential facts,
- no substantial management/classification/pitfall material beyond one teaching point.

Use `core` when the source case is dense:
- multiple modalities, phases, planes, or image groups,
- rich differential diagnosis requiring discrimination,
- useful Essential Facts beyond the diagnosis,
- Other Imaging Findings that change interpretation or follow-up,
- Pearls/Pitfalls that are clinically important,
- management, prognosis, complication, or classification points worth testing.

### RadCases Short Case conversion
- Follow the general Short Cases Prompt exactly: **3-5 questions**, image-led, diagnosis-blinded before diagnosis, varied stems, no options in `question_text`, and balanced SC multiple-choice answer counts and positions.
- A typical RadCases SC should include:
  1. clinical vignette from Clinical Presentation,
  2. localisation or key abnormality question using question-page image(s),
  3. imaging feature or differential question,
  4. diagnosis question, unless the differential question already functions as the diagnostic question,
  5. optional post-diagnosis pearl, pitfall, other-imaging, or essential-fact question.
- Do not convert every RadCases SC into the same four questions. The source sections determine which question types are useful.
- Before drafting a 10-case RadCases batch, assign a planned question count for each SC case. A normal
  batch should visibly mix 3-, 4-, and where supported 5-question SCs. If all or nearly all SC cases have
  four questions, the batch fails validation unless the source is genuinely uniform and sparse.
- Use 3 questions for focused spotters with limited teaching material; use 4 questions for ordinary short
  cases; use 5 questions only when the source provides a worthwhile pearl, pitfall, other-imaging, or
  essential-fact target that does not duplicate the diagnosis/finding questions.

### RadCases CORE conversion
- Follow the general CORE Cases Prompt exactly, but for RadCases keep CORE cases to **4-6 questions**
  rather than the generic 4-7 range. Use long-case style, no diagnosis leakage, structured use of free-text /
  single-choice / multiple-choice, plausible same-domain distractors, and no unsupported facts.
- A RadCases CORE case should deliberately test more of the answer page than an SC case. It should normally include:
  - Q1/Q2: key imaging findings, staged by modality or image group when appropriate.
  - Diagnosis or differential question using the source Differential Diagnosis section.
  - At least two source-supported teaching targets from Essential Facts, Other Imaging Findings, Pearls/Pitfalls, management, complications, prognosis, anatomy, or classification.
- For RadCases CORE cases, review all question-page and answer-page images before drafting the imaging
  questions. If the case contains different modalities or clearly separate image groups, split them into
  separate imaging questions instead of merging them into one generic findings question. Examples:
  chest radiograph vs CT, echocardiography vs CTA/MRI, angiography vs CT, CT vs MRI, pre-contrast vs
  post-contrast, arterial vs venous/delayed phase, or baseline vs follow-up images.
- Each staged imaging question should receive only the relevant `page_images` for that modality/image
  group. The corresponding answer-side clinical or annotated images for that modality/image group should
  go in that question's `answer.page_images`.
- Combine modalities into one findings question only when the source is sparse, when the additional
  modality simply repeats the same finding without adding a separate interpretive task, or when splitting
  would force padding beyond source support.
- Keep diagnosis-blinding intact when staging modalities: do not attach labelled or answer-revealing
  answer-page images to pre-diagnosis question images.
- Named-diagnosis facts belong after the diagnosis question unless the diagnosis question is omitted because the case is primarily a differential/mapping exercise.
- Before drafting a 10-case RadCases batch, assign a planned question count for each CORE case. A normal
  batch should not cluster every CORE case at the same length; mix 4-, 5-, and 6-question CORE cases
  according to source density.
- Use 4 questions for compact CORE-style cases, 5 questions for standard dense cases, and 6 questions only
  when the answer page contains several distinct high-yield targets. Do not pad beyond source support.

### Image handling
- Question-page clinical images go into question `page_images`.
- Answer-page labelled, repeat, explanatory, or teaching images go into answer `page_images`.
- Include all relevant clinical images from the relevant page; never select only a representative subset.
- Do not attach answer-page labelled images to pre-diagnosis questions if they reveal the diagnosis or answer.
- If one source case has multiple modalities or clearly separate image groups, stage them across questions using the general SC/CORE multi-modality rules.
- If PyMuPDF exposes a full-page scan, watermark, logo, or decorative non-clinical object, visually inspect before deciding whether to omit it.

### Validation before insertion
- Validate each 10-case batch before insertion.
- Confirm every source case has exactly one output case and that the batch has at least 3 CORE cases when it contains 10 cases.
- Validate all usual SC/CORE requirements: sequential `q_number`s, **3-5 SC questions**, **4-6 RadCases
  CORE questions**, no pre-diagnosis leakage, no options inside `question_text`, exactly 5 options for choice
  questions, single-choice answer text present in options, and multiple-choice `correct_options` length 1-4.
- For RadCases, validate **semantic diagnosis blinding** explicitly. Before the diagnosis question, imaging
  stems must be generic only. Use stems such as:
  - "Describe the imaging findings."
  - "Describe the CT findings."
  - "Describe the MRI findings."
  - "Describe the radiographic findings."
  - "Indicate the abnormality."
  Do not include anatomical localisation, organ/system labels, vessel names, compartment labels,
  pathology-class labels, mechanism labels, exposure labels, or pattern labels before the diagnosis is asked.
  Avoid pre-diagnosis wording such as "vascular", "aortic", "coronary", "pulmonary arterial", "venous",
  "airway", "pleural", "mediastinal", "parenchymal", "cystic", "fibrotic", "traumatic", "postoperative",
  "postsurgical", "endovascular", "sarcoid-related", "asbestos-related", "sickle-cell acute chest",
  "bronchiectatic", or "postemetic". These details belong in the answer, explanation, post-diagnosis
  teaching questions, or diagnosis options, not in a pre-diagnosis stem. If a pre-diagnosis stem is more
  specific than the modality or "abnormality", rewrite it before insertion.
- Validate planned question-count variation across the batch. If SCs are all/nearly all 4-question cases, or
  CORE cases all/nearly all have the same number of questions, the batch fails validation and must be revised
  before insertion.
- Apply the existing SC multiple-choice distribution and a-e position rules to SC questions in the batch.
- Apply the same balanced multiple-choice principles to CORE multiple-choice questions; avoid predictable all-true or front-loaded answer patterns.
- Validate that each case considered Differential Diagnosis, Imaging Findings, Essential Facts, Other Imaging Findings, and Pearls/Pitfalls, and that clinically useful content from those sections appears in the questions or explanations.
- Store backup DB copies and temporary JSON/extraction files only under `C:\Users\Razvan\Documents\Radiologie\backups`.

---

## Book-Specific Tips: Modern Radiology eBook (ESR)

### Source and section
- Use `"source": "Modern Radiology eBook"`.
- Use `"section": "mrq"` for all imports from this eBook series.
- Generate MRQs from each PDF according to that PDF's actual topic and educational content.

### Book structure
- Modern Radiology eBook PDFs are slide-style/theory chapters with compact pages, figures, icons,
  take-home messages, references, and native `Test Your Knowledge` sections.
- Skip non-educational pages: cover, preface, copyright/terms, signage/icon explanation, authors/affiliations,
  references-only pages, and duplicated answer pages except as answer-key confirmation for `Test Your Knowledge`.
- Use educational content from main theory pages, `CORE KNOWLEDGE`, `FURTHER KNOWLEDGE`, `ATTENTION`,
  `COMPARE`, figures/captions, take-home messages, and native `Test Your Knowledge` question/answer pairs.

### Chapter routing
- Route each Modern Radiology PDF by content, not by source label.
- CT/MRI/US technique, scanner physics, image acquisition, reconstruction, artefacts, modality principles
  -> `Physics, Principles of Imaging Techniques, and Informatics`.
- Contrast agents, contrast reactions, NSF, extravasation, and renal-risk logic -> `Safety in Radiology`.
- Radiation biology/protection/dose-risk material -> usually `Safety in Radiology`; use `Physics` only when
  the emphasis is technical dosimetry rather than patient/staff safety.
- Organ-based PDFs -> the corresponding organ chapter.
- Hybrid, nuclear, PET, and SPECT content -> `Hybrid Imaging`.
- Communication, reporting, management, and informatics workflow -> `Communication and Management` or
  `Physics, Principles of Imaging Techniques, and Informatics` depending on dominant content.
- For `Computed Tomography.pdf`, route all generated MRQs to chapter 12 with `"chapter_match": "exact"`.

### MRQ density
- Use content density, not a fixed per-PDF quota.
- Default target: **10-15 MRQs per 10 meaningful content pages**.
- Count only meaningful educational pages: theory, figures/captions, take-home messages, and question pages.
- Do not count cover, preface, copyright, signage, authors, references-only pages, or duplicated answer pages
  as content.
- Dense sections with diagrams, artefacts, protocols, modality comparisons, safety algorithms, classifications,
  or strong take-home bullets may approach 15 MRQs per 10 pages.
- Sparse, image-only, or low-yield pages may generate fewer, including zero.
- Never pad to hit a number.
- For `Computed Tomography.pdf`, expect roughly **45-60 MRQs**, depending on extraction quality and density.

### MRQ generation rules
- Generate proper EDiR-style MRQs:
  - `q_type`: `"multiple_choice"`.
  - Exactly 5 options.
  - `correct_options` as 0-based indices.
  - No shared clinical vignette unless an image-based question needs short context.
  - No option text embedded in `question_text`.
  - No negative stems such as "Which is wrong?", "Which is not correct?", or "Which are not correct?".
- Emphasise applied radiology-facing skills:
  - choosing or understanding modality/protocol logic
  - artefact recognition and correction
  - acquisition, reconstruction, and windowing tradeoffs
  - safety and dose reasoning where clinically meaningful
  - modality comparisons
  - anatomy/image navigation when relevant
  - interpretation consequences of technical choices
- Avoid low-value rote memorisation:
  - Do not ask isolated trivia just because it appears in the source.
  - Numbers are allowed only when practically important and source-grounded.
  - Preserve exact source numbers when used.
- Apply all general MRQ rules: source-grounding, positive stems, fair 1-4 correct-answer distribution,
  balanced a-e answer positions, and a compact blueprint before drafting.

### Native Test Your Knowledge handling
- Use native `Test Your Knowledge` items as seed material, not verbatim imports.
- Convert 4-option single-best-answer items into 5-option multiple-select MRQs.
- Use the answer page only to confirm the source-supported truth.
- Add the fifth option from nearby source text or a source-grounded distractor.
- Rewrite single-best stems into "Which statements are correct?" style.
- Rewrite negative stems into positive MRQ stems.
- Do not duplicate question and answer pages as separate content sources.

### Images
- Use images only when educationally needed.
- Include diagrams, anatomy figures, artefact examples, modality schematics, and labelled CT/MRI/US images
  when the MRQ depends on them.
- Skip decorative cover art, icon/signage graphics, logos, and purely layout images.
- Visually map image indices to the correct figure/caption before assigning `page_images`.
- Do not use a rigid 200 px cutoff; small diagrams may be educational.
- Omit `original_answer_pages` for MRQ imports unless a future PDF has a discrete answer-page structure
  that is useful for review.

### Validation before insertion
- Validate the correct source label: `"Modern Radiology eBook"`.
- Validate correct chapter routing for the PDF topic.
- Validate all cases use `"section": "mrq"`.
- Validate every choice question has exactly 5 options.
- Validate every question uses a positive MRQ stem.
- Validate no option text is embedded in stems.
- Validate no unsupported facts or outside knowledge were added.
- Validate fair correct-answer count distribution across 1-4 correct options and balanced answer positions
  across a-e.
- Validate images are relevant and non-decorative.
- Validate native `Test Your Knowledge` items were converted into MRQs, not copied as 4-option SBAs.
- Store backup DB copies and temporary JSON/extraction files only under `C:\Users\Razvan\Documents\Radiologie\backups`.

---

## Book-Specific Tips: Scientific Articles (`Articole Tdi` PDFs)

### Source and section
- Use `"source": "Scientific articles"`.
- Use `"section": "mrq"`.
- One article PDF = one MRQ session/case.
- Route each article by its actual topic to the most appropriate existing EDiR chapter.
- Put the article title in `clinical_vignette`.
- Every Scientific Articles MRQ session must include a case-level `article_summary` field.

### Article structure and source use
- Use the article as the only ground-truth source.
- Prioritise the title, abstract, key points, tables, figures/captions, guideline boxes, algorithms,
  conclusions, and radiology-facing discussion.
- Skip low-yield material: author lists, affiliations, methods detail, publication metadata,
  references, journal formatting, and p-values/sample sizes unless they are clinically central.
- These are concise article takeaways, not exhaustive textbook-style coverage.
- If text extraction is poor, use OCR or visual inspection before generating questions.

### Article summary / resume
- After drafting and validating the MRQs, create a 1-2 page Markdown article summary in `article_summary`.
- Normal length: roughly **700-1200 words** for a typical article. Short focused articles may be shorter; very dense guidelines may approach the upper end, but do not pad.
- The summary should help the learner remember the article after answering the MRQs. It appears only in review mode, after the questions.
- Start every article summary with a short metadata block:
  - `### Article`
  - `**Title:** <full article title>`
  - `**Authors:** <authors as listed in the article>`
  - `**DOI:** <https://doi.org/...>` when a DOI is present in the article; if no DOI is present, write `Not stated in the PDF`
- Use a concise structure such as:
  - `### Why this article matters`
  - `### Key imaging points`
  - `### Practical reporting or management implications`
  - `### Pitfalls and limitations`
  - `### Take-home points`
- Prioritise radiology-facing content: imaging criteria, protocol or modality choice, classifications, algorithms, reporting consequences, pitfalls, mimics, false positives/negatives, and management-changing findings.
- Do not summarise author metadata, methods minutiae, journal formatting, references, or statistics unless they are central to the clinical conclusion.
- Do not introduce outside facts. Do not copy long article passages verbatim. Paraphrase the article's practical conclusions.

### MRQ density
- Use article density, not a fixed quota.
- Short/focused articles: **4-5 MRQs**.
- Typical educational or pictorial review articles: **5-6 MRQs**.
- Dense guideline/classification articles: **8-10 MRQs**.
- Very large guidelines or major consensus documents: **10-12 MRQs**, or split into separate article
  sessions only when needed to preserve quality.
- Never pad to hit a quota. If the source supports fewer high-yield radiology questions, generate fewer.
- If the user writes "45 MRQs" in this context, interpret it as **4-5 MRQs** unless they explicitly
  request forty-five questions.

### MRQ generation focus
- Generate EDiR-style MRQs focused on radiologist decision-making:
  - imaging criteria and thresholds
  - modality/protocol choice
  - guideline applicability and exclusions
  - classification/reporting implications
  - key pitfalls, mimics, and false positives/false negatives
  - management-changing imaging findings
  - communication, safety, and error-prevention behaviours for non-organ articles
- Avoid journal-club trivia and word-by-word memorisation.
- Do not ask about author names, publication dates, affiliations, sample size, p-values, or study design
  details unless the article's main radiology conclusion depends on them.
- Do not turn the article methods into MRQs. A question whose main learning target is "how the study was
  designed", "how lesions were counted", "which statistical test was used", "which reader measured what",
  or "which reference region was used" is usually low yield and should be rejected.
- Use methods details only as background to judge whether a clinical conclusion is trustworthy. The visible
  MRQs should test the general radiology lesson a reader should retain after the article: how to interpret an
  imaging finding, when a test/tracer/protocol is useful, what a result changes in reporting or management,
  what pitfall to avoid, or what practical conclusion should not be overextended.
- Before finalising each article MRQ, ask: "Would this help me report, protocol, choose imaging, avoid an
  interpretive pitfall, or discuss management?" If the answer is no, rewrite or delete the question.
- Do not use article-referential wording in visible question stems, options, or explanations. Avoid phrases such as
  "according to this article", "in this study", "the authors concluded", "this article should influence",
  "the paper shows", "the study found", "the source comparison", or "the source premise". The article is the
  hidden ground-truth source, but the learner-facing MRQ must read like general EDiR/radiology knowledge.
- Phrase stems as durable clinical knowledge, e.g. "Regarding somatostatin receptor PET/CT in neuroendocrine
  tumours..." rather than "Regarding the findings of this article...".
- Apply all general MRQ rules: positive stems, exactly 5 options, no option text in `question_text`,
  1-4 correct answers, source-grounded explanations, balanced a-e positions, and the blueprint checkpoint.

### Correct-answer distribution for short article sessions
- For 4-question article sessions, include at least two different correct-answer counts.
- For 5-6-question article sessions, aim to include 1-, 2-, 3-, and 4-correct questions when
  source-supported.
- Do not make every article session mostly 3- or 4-correct.
- Before drafting each article's MRQs, write the compact blueprint showing intended correct-answer count
  and rough answer positions for every question, even when there are only 4-6 questions.

### Chapter routing
- Pulmonary/chest articles -> `Chest and Thorax Radiology`.
- Breast articles -> `Breast Radiology`.
- CNS/head-neck articles -> `Neuroradiology` or `Head and Neck` as appropriate.
- Vascular/interventional articles -> `Interventional and Vascular Radiology`.
- GU/GI/MSK/Cardiac/Paediatric articles -> matching organ chapter.
- PET/SPECT/hybrid articles -> `Hybrid Imaging`.
- Radiation protection, contrast safety, MRI safety, and gadolinium risk -> `Safety in Radiology`.
- Diagnostic error, communication, patient expectations, and radiologist role -> `Communication and Management`.
- Imaging protocols and technical modality articles -> `Physics, Principles of Imaging Techniques, and Informatics`.

### Images
- Omit images unless a figure is essential to answer the MRQ.
- If a figure is used, visually map the image to the exact figure/caption before assigning `page_images`.
- Do not use decorative images, journal logos, flowery cover art, or answer-leaking composites.
- Do not use `original_answer_pages` for scientific article MRQ imports.

### Validation before insertion
- Validate the exact source label: `"Scientific articles"`.
- Validate all cases use `"section": "mrq"`.
- Validate chapter routing matches the article topic.
- Validate the question count fits article density and is not padded.
- Validate every option and explanation is supported by the article.
- Validate no negative stems, no embedded options, and exactly 5 options per question.
- Validate correct-answer counts and a-e positions are varied enough for the article size.
- Validate images are omitted unless essential, relevant, non-decorative, and not answer-leaking.
- Validate `clinical_vignette` contains the article title.
- Validate `article_summary` is present, source-grounded, paraphrased, and focused on practical points to remember.

---

## Book-Specific Tips: Core Radiology (Cambridge University Press, 2021)

### Book structure
- Core Radiology is a **theory textbook**, not a case book. Pages mix dense bullet-point theory with inline clinical images and their captions — there is no separate "case page / answer page" structure.
- All imports from this book use `"section": "mrq"`. Do not generate CORE or SC cases from it.
- Content is organised by body system and topic within each chapter. Each chapter corresponds to one DB chapter (use `"chapter_match": "exact"` where the topic maps clearly).

### Page offset (GU chapter — verify for other chapters)
- GU chapter: GU printed page 229 = PDF page 0.
- Formula: `PDF_0based = printed_page − 229`.
- Always verify the offset for each chapter before computing all image/page references.

### TOC and title pages
- The first PDF page of each chapter is a title/TOC page — skip it entirely. Generate no questions from it.

### Image handling
- The ≥200 px rule works reliably for this book — **no visual inspection needed**. There are no decorative overlays or full-page scan backgrounds.
- Images are inline theory illustrations, not standalone case images. Each image has a caption in the extracted text (e.g. "Retroperitoneal fibrosis: Axial CT shows...") that names the finding or diagnosis.
- **Template A context** comes directly from the image caption — write a blinded paraphrase of the caption as the clinical context (omit the diagnosis name if it gives away the answer).
- A single page may contain images for multiple distinct topics at non-sequential indices. Always extract image indices via PyMuPDF before writing questions and map each index to its caption:
```python
for p in [page_list]:
    imgs = doc[p].get_images(full=True)
    for i, img in enumerate(imgs):
        pix = fitz.Pixmap(doc, img[0])
        print(f'  [{i}] xref={img[0]} size={pix.width}x{pix.height}')
```

### Question generation
- The book's bullet-point format maps naturally to MRQ options: each bullet is a directly testable statement.
- **Radiology skill focus:** MRQs should primarily test radiological reasoning, image interpretation,
  protocol selection, anatomy, differential diagnosis, staging, and management implications. Do not turn
  every paragraph into factual recall or word-by-word memorisation. Prefer questions that require applying
  source facts to a radiology task: identifying the relevant imaging feature, distinguishing similar diagnoses,
  choosing the correct protocol or phase, interpreting thresholds in clinical context, recognising staging
  implications, or selecting the next imaging/management step implied by imaging. Use exact source facts as
  ground truth, but phrase options as clinically useful radiology statements rather than copied textbook
  bullets. A good MRQ should feel like: "Can I use this fact at the workstation or in an exam case?", not:
  "Can I recite this paragraph?" Avoid low-value recall unless the number, classification, or threshold is
  genuinely exam-relevant or needed for radiology decision-making.
- **Distractor strategy — prefer cross-passage attribution over inversion:** The best distractors are real statements from a *different* section of the same chapter, presented as if they apply to the current topic. For example, a feature of pheochromocytoma used as a distractor in an adrenal adenoma question. This produces distractors that are never fabricated, are harder to dismiss by logic alone, and test integration across the chapter rather than recall of one passage. To do this effectively, read (or have extracted) the full chapter text before generating questions, so a pool of real cross-section statements is available.
- **Fallback distractor techniques** (when cross-passage material is unavailable or insufficient): invert a specific detail from a correct statement (swap "anterior"/"posterior", negate a relationship, flip "most"/"least"); or corrupt an exact number by shifting a threshold or percentage. Use these only when a genuine cross-passage distractor cannot be found.
- **Correct-answer distribution must be planned before drafting options:** Core Radiology MRQs must not
  become "four true, one false" by habit. Before writing the options for a batch, assign each planned
  question an intended number of correct answers and rough correct-answer positions. Then draft that
  question to meet the assigned count from the start. Do not first collect five true textbook bullets and
  try to rebalance afterwards.
  - For ~20 questions, aim for roughly: 1 correct = 2-3 questions; 2 correct = 5-6; 3 correct = 7-8;
    4 correct = 3-5.
  - For ~15 questions, aim for roughly: 1 correct = 1-2 questions; 2 correct = 4-5; 3 correct = 5-6;
    4 correct = 3-4.
  - For ~30 questions, aim for roughly: 1 correct = 4-5 questions; 2 correct = 8-9; 3 correct = 10-11;
    4 correct = 5-6.
  - If the batch has >=10 questions, it should normally include at least one 1-correct question and at
    least two 2-correct questions.
  - No single correct-answer count should dominate the batch unless the source genuinely forces it.
  - 4-correct questions are allowed, but they should be a minority rather than the default.
- **Per-question drafting order:** For each MRQ, choose (1) the tested radiology concept, (2) the intended
  number of correct answers, (3) the intended correct-answer positions, and (4) the source-grounded
  distractor pool before writing the five options.
- **Distractors are part of first drafting, not a cleanup step:** If a question is planned to have 1 or 2
  correct answers, build plausible false options from cross-passage attribution or source-grounded
  inversion immediately. Do not reduce the correct-answer count later by merely changing
  `correct_options`.
- **Hard final distribution audit before insertion:** Before writing the final JSON or inserting into the
  DB, calculate the number of questions with 1, 2, 3, and 4 correct answers. If the batch fails the planned
  distribution above, revise the visible option text, `options` array, `correct_options`, and explanation
  before insertion. Do not proceed with insertion until the distribution is acceptable.
- **Correct-answer distribution:** Core Radiology MRQs must not become "four true, one false" by habit.
  Before finalising a batch, audit `correct_options` lengths and revise options so the batch contains a
  realistic spread of 1-, 2-, 3-, and 4-correct questions. Prefer 2–3 correct answers for many questions,
  with occasional 1- and 4-correct questions when the source supports them. Do not create false
  distractors by inventing facts; use cross-passage attribution or source-grounded inversion instead.
- **Correct-answer position distribution:** Spread correct answers across positions a–e — do not draft correct statements first and distractors last. Each position should be correct in roughly 40–65% of questions across a batch. Deliberately assign correct options to later positions (c, d, e) as often as to a and b.
- **Exact numbers are authoritative**: this book is unusually precise (e.g. 70–80%, 20–30%, 90% benign, 66% functional, 1/1,000,000). Reproduce them verbatim — do not round or substitute.
- The temptation to add well-known radiology facts not present in the extracted text is high for a theory book at this level. Apply the anti-hallucination rules strictly: if a fact is not in the extracted text, omit it.
- Skip or generate very few questions for sparse pages (diagram-label-only pages, image-only pages). Do not pad.

### Batching for long chapters
- Process ~12 pages per batch. Generate ~20-25 questions for ordinary density, and up to ~30 questions when the same page range is genuinely dense enough. Do not enlarge batches merely to reach 30 questions.
- **Each batch = one case object (one MRQ session).** Do not accumulate all batches into a single case object for the whole chapter — each batch stands alone.
- Insert each batch's JSON into the DB as it is completed. Do not wait until all batches are done.
- At the start of each batch session: read `import_prompts.md`, extract text and image indices for the current page range, then generate questions strictly from that extracted content.

<!-- CLAUDE-ONLY: workflow notes — not relevant to other LLMs or the insertion pipeline -->
<!-- 1. Output structure: one JSON array with one case object per batch. Do not merge batches into one case. -->
<!-- 2. Generation order: write all questions first, then do a single pass to audit correct-answer position distribution and swap option order on individual questions if needed. Do NOT pre-plan the answer key for all questions before writing options — that loop never terminates. -->
<!-- 2A. Current override: pre-plan each question's target correct-answer count and rough positions before drafting options; the old no-preplanning note above is superseded by the visible general MRQ blueprint rule. -->
<!-- 3. Extraction strategy: extract text and image indices for the batch pages in one script call, then generate all questions from that output. Do not re-extract mid-batch. -->
<!-- 4. If position distribution is still off after one audit pass, fix the worst offenders and move on. Do not iterate the audit more than once. -->

---

## Book-Specific Tips: Top 3 Differentials in Radiology (Thieme, 2nd ed.)

### Source and section
- Use this book to create **Short Cases** only: `"section": "sc"`.
- One source book case = one app short case. Do not merge several book cases into one app case.
- Suggested source label: `"Top 3 Differentials in Radiology"` unless the user asks for a different app label.

### Book structure
- The PDF has a reliable TOC/bookmarks and clean text extraction.
- There are 330 cases. Most cases follow a highly regular 2-page pattern:
  - Page 1: case number, clinical presentation, clinical image(s), and image caption.
  - Page 2: key imaging finding, top 3 differential diagnoses, additional differential diagnoses, diagnosis, pearls, and suggested readings.
- Set case-level `original_answer_pages` to the second/source answer page for each case; do not include suggested-reading-only pages.
- Ignore front matter, indexes, and suggested readings.
- Use the clinical presentation, figure caption, key imaging finding, top 3 differentials, diagnosis, and pearls as the source material.

### Chapter routing
- Decide the DB chapter **per case**, not just from the book part title.
- Use the image finding, diagnosis, and anatomic system to choose the best EDiR DB chapter.
- Default routing by part:

| Book part | Cases | Default DB chapter |
|-----------|-------|--------------------|
| Chest and Cardiac Imaging | 1-30 | Chest and Thorax Radiology, but route cardiac cases to Cardiac Radiology and acute aortic/vascular cases to Interventional and Vascular Radiology when appropriate |
| Gastrointestinal Imaging | 31-55 | Abdominal Radiology |
| Genitourinary Imaging | 56-80 | Genitourinary Radiology |
| Musculoskeletal Imaging | 81-105 | Musculoskeletal Radiology |
| Head and Neck Imaging | 106-130 | Head and Neck, but route intracranial/dural/leptomeningeal cases to Neuroradiology when appropriate |
| Brain and Spine Imaging | 131-155 | Neuroradiology |
| Pediatric Imaging | 156-180 | Pediatric Radiology unless the case is clearly better tested as a subspecialty adult-style topic |
| Ultrasound Imaging | 181-205 | Mixed; route by anatomy/diagnosis per case |
| Fetal Imaging | 206-230 | Pediatric Radiology by default; route maternal/placental/gynaecologic topics by best fit if needed |
| Vascular and Interventional Radiology | 231-255 | Interventional and Vascular Radiology |
| Nuclear Medicine | 256-280 | Hybrid Imaging |
| Breast Imaging | 281-305 | Breast Radiology |
| Roentgen Classics | 306-330 | Mixed; route by anatomy/diagnosis per case |

- If a book part mixes systems, split/reroute individual cases. Do not force everything in that part into one chapter.
- Use `"chapter_match": "exact"` when the case clearly belongs to the selected chapter; use `"close"` only when the best EDiR chapter is a pragmatic nearest fit.

### Short-case conversion template
- Preserve the book's spotter logic: image first, abnormality/key finding, top differential, diagnosis, then teaching pearl.
- Typical app structure, not a mandatory template:
  1. **Clinical vignette**: use the book's "Clinical Presentation". Keep it short and do not reveal the diagnosis.
  2. **Q1**: `"Indicate the abnormality."` `[free_text]`
     - Answer from "Key Imaging Finding" plus precise location from the caption.
     - Attach the case image(s) to this question.
  3. **Q2**: imaging findings question `[multiple_choice | free_text]`
     - Use source-supported findings from the caption and differential text.
     - Before the diagnosis question, keep this diagnosis-blinded. Example stems:
       "Which radiological findings are demonstrated?" or
       "Which imaging features help characterise this pattern?"
     - Do not ask "Which findings support [final diagnosis]?" before the diagnosis has been asked.
  4. **Q3**: top differential question `[free_text | multiple_choice]`
     - Prefer `free_text` for "List the top 3 differential diagnoses" because this is the book's core educational structure.
     - Use `multiple_choice` when the source supports testing the recognised differentials against plausible same-domain alternatives.
  5. **Q4**: diagnosis question `[single_choice]`
     - Use the source-stated "Diagnosis" as the correct answer.
     - Use close imaging/clinical mimics as distractors, ideally from the top 3/additional differentials.
  6. **Q5 optional**: targeted pearl, complication, management, or distinguishing-feature question `[multiple_choice | single_choice | free_text]`
     - Use only when the "Pearls" or differential discussion contains a useful EDiR-level teaching point.
- Not every case needs all five questions. Generate fewer if the source is sparse, but one book case should still become one coherent short case.
- Do not convert every Top 3 book case into the same four app questions. For each 10-case batch, deliberately
  mix the structures:
  - some cases should be concise 3-question spotters (localisation/key abnormality + differential or diagnosis + one focused pearl),
  - many cases can be 4-question short cases,
  - some dense or multimodality cases should have 5 questions when the source supports a meaningful extra step.
- In each 10-case batch, use at least three different Q2/Q3 stem families unless the source is genuinely too
  repetitive. Include some `multiple_choice` top-differential selection questions, not only generic
  "which findings support" or "which statements are correct" questions.
- Prefer source-shaped questions over template-shaped questions. If the book case centres on a ranked top 3
  list, test top differentials. If it centres on a key imaging sign, test the sign and its mimics. If it centres
  on a practical pearl, test that pearl. If it only supports a simple diagnosis, keep the case shorter.
- Preserve diagnostic suspense. For Top 3 short cases, do not name the final diagnosis in Q2/Q3 stems if Q4 is
  still going to ask for the diagnosis. Use neutral stems such as "this pattern", "this appearance", "the
  demonstrated abnormality", or "the leading mimic group" until the diagnosis question has been answered.
- If you want to ask a named-diagnosis feature question, put it after the diagnosis question as a post-diagnosis
  pearl, or remove the separate diagnosis question because the diagnosis has already been revealed.

### Image handling
- Images are usually clean clinical image objects on the case/presentation page. Include all clinical images from that page in the relevant question `page_images`.
- Do not include images from indexes, title pages, or suggested reading sections.
- If a figure is a composite image object containing several labelled panels, include it as one image if that is how PyMuPDF exposes it.
- Captions may reveal the diagnosis or key abnormality; use them as ground truth for answers, but do not copy diagnosis-revealing caption text into the question stem.

### Multi-modality image staging
- If a short case contains multiple modalities, phases, sequences, or clearly different image groups, stage the images across questions instead of attaching all images to Q1.
- Q1 should use the easiest/localising first-look image, usually the radiograph, ultrasound overview, or initial CT/MRI slice, and ask: `"Indicate the abnormality."`
- Q2 should use the second modality or characterising/problem-solving images and ask for key findings, e.g. `"Describe the key findings on CT/MRI/US"` or `"Which imaging features are demonstrated on the second modality?"`
- Keep same-modality panels together when they represent one figure set or the same finding in different planes.
- Do not split images arbitrarily: split only when the source case naturally separates modalities, phases, sequences, or overview vs problem-solving images.
- If all images are needed to recognise the abnormality, attach them all to Q1.

### Question style
- The primary educational target is differential diagnosis skill:
  - recognise the key abnormality,
  - build the top differential,
  - distinguish the leading diagnosis from close mimics,
  - retain one practical pearl.
- Keep explanations short and tied to the source. Do not import extensive outside knowledge.
- Do not turn every case into a long CORE case. These are short cases: focused, quick, and image-led.
- Avoid padding. If the case only supports three strong questions, stop at three.
- Before inserting a Top 3 batch, audit **question-style distribution** in addition to correct-count and
  answer-position distribution. A valid batch should not have all cases with identical question counts or the
  same repeated Q2/Q3 phrasing. If the batch is structurally monotonous, it fails validation and must be revised.
