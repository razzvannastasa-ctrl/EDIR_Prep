# CORE Case Improvement Prompt

*Use this when auditing and improving existing CORE cases in the database. This is not an import prompt and should not generate new cases from scratch.*

---

## Objective

Improve existing CORE cases so they feel closer to official EDiR CORE cases:

- staged clinical reasoning
- typed answers for the most markable reasoning step in the case, such as findings, differentials, diagnosis, management, complications, staging, or report recommendation
- selective single-choice and multiple-choice questions where choice format is natural
- concise, markable answers based on the source answer page
- no invented content

This workflow applies primarily to CORE cases where `source != "Essential Guide"`, unless the user explicitly requests otherwise.

---

## Ground Rules

1. Preserve the case identity.
   - Do not merge, split, reorder, or delete cases unless explicitly requested.
   - Keep `case_id`, `source`, `chapter_id`, `section`, and `case_number` stable.

2. Use source material as ground truth.
   - Reread the existing clinical vignette, questions, answers, explanations, question images, and attached answer page images.
   - If original answer pages are available, use them as the authoritative source.
   - Do not add external medical facts unless the existing answer content already supports them.

3. Make minimal, high-value changes.
   - The goal is not to rewrite every question.
   - Prefer 1-2 meaningful conversions per case.
   - Do not always target the diagnosis question for free-text conversion.
   - Vary the free-text target according to the answer page and the case flow.
   - Leave good choice questions as choice questions.

4. Keep the exam feel.
   - Official CORE cases are usually staged: clinical data first, then findings, differential/diagnosis, and management or teaching point.
   - Avoid textbook-style or generated language.
   - Avoid "source-supported", "according to the source", "model answer", "which statements are true", unless that wording is present in the original educational source and is clearly useful.

5. Do not change images unless the audit finds a concrete issue.
   - If image crops are wrong, missing, or assigned to the wrong question, fix them in a separate image repair step.
   - If a later question still depends on earlier images, it is acceptable to repeat the same image paths on that later question.

---

## Official CORE Style Target

Use this pattern as the target style:

1. Clinical data page:
   - short patient age/sex/context
   - relevant presentation and prior history
   - modality requested/performed
   - no diagnosis revealed

2. Early imaging question:
   - usually free text
   - asks for relevant findings
   - answer is short and markable

3. Localisation, differential, or diagnosis question:
   - may be free text for diagnosis, top differentials, localisation, or key features
   - may stay choice-based if the options are plausible and educational
   - if diagnosis stays choice-based, a differential, findings, or management question can be the better free-text target

4. Later management or knowledge question:
   - single-choice or multiple-choice if there is a clear option set
   - free text if management, complications, staging, or report wording is a short markable answer

5. Review answer:
   - correct answer first
   - marking criteria or accepted alternatives where useful
   - concise explanation

---

## When to Convert Choice Questions to Free Text

Convert a `single_choice` or `multiple_choice` question to `free_text` when the official CORE format would naturally expect a typed answer.

Do not automatically choose one question type or one question position. For Q3+ free-text conversions, balance the selected targets by percentage across the batch.

Good conversion categories:

- Findings or localisation when the source expects a short description.
- Diagnosis when the source answer is a concise diagnosis or accepted synonym list.
- Differential diagnosis when the source gives top differentials or ranked alternatives.
- Management or report recommendation when the source expects a short practical recommendation.
- Complications when the source gives a short list, such as top complications to consider.
- Staging, classification, or grading when the source gives a concise markable category.
- Associations, risk factors, or key teaching points when the source gives a short markable list.

Later free-text target families:

- `diagnostic_reasoning`: direct diagnosis, differential diagnosis, localisation, classification/staging, or discriminating features.
- `management`: next step, treatment, report recommendation, or follow-up.
- `complication_teaching`: complications, pitfalls, associations, epidemiology, or clinical pearls.

For Q3+ free-text conversions, aim for 33% per family across the batch. The acceptable range is 30-35% per family when the source supports it. Q1/Q2 findings are excluded from this calculation.

Good conversion candidates:

- `Describe the imaging findings.`
- `Where is the abnormality?`
- `Give the most likely diagnosis.`
- `What are the two most likely differential diagnoses?`
- `What would you recommend in the report?`
- `What is the next management step?`
- `What follow-up is appropriate?`
- `Name the top three complications.`
- `What pitfall should be considered?`
- `What stage/classification best applies?`

Do not convert automatically. Convert only when the answer page contains a clear short answer or a markable list.

Decision rules:

1. Choose the shortest answer-page item that can be marked fairly.
2. Direct diagnosis free text is valid and counts as `diagnostic_reasoning`.
3. Diagnosis may be `free_text`, `single_choice`, or `multiple_choice`, depending on which format best tests the case.
4. If diagnosis stays choice-based, differential diagnosis, localisation, classification/staging, or discriminating features can still satisfy `diagnostic_reasoning`.
5. Do not let management or pitfall questions absorb most conversions just because they are easy to mark.
6. Across the batch, deliberately choose Q3+ free-text targets so `diagnostic_reasoning`, `management`, and `complication_teaching` each land near 33%, with 30-35% acceptable.

Preferred free-text stems:

- `Describe the findings.`
- `Describe the most relevant imaging findings.`
- `Give the most likely diagnosis.`
- `Based on the images and clinical findings, give the two most likely diagnoses.`
- `What are the differential diagnoses?`
- `What would you recommend in the report?`
- `What is the next management step?`
- `What follow-up is appropriate?`
- `Name the most important complications.`
- `What pitfall should be considered?`
- `What classification or stage applies?`

Answer format for converted free-text questions:

- short phrase, line, or bullet list
- include accepted alternatives where present
- no long textbook paragraph in `answer_text`
- put reasoning and teaching points in `explanation`

Example:

```text
answer_text:
Papillary renal cell carcinoma

explanation:
Accept renal tumour in the left kidney for partial credit. The imaging shows a solid renal lesion with restricted diffusion and low T2 signal, which favours papillary RCC over a simple cyst.
```

---

## When to Keep Choice Format

Keep `single_choice` when:

- there is one best next test or one best management option
- the official-style task is explicitly "Only one option is correct"
- the diagnosis choices are plausible close mimics and the answer page has a better free-text target elsewhere
- staging/classification/modality selection works better as an option set
- the wrong options are plausible and educational

Keep `multiple_choice` when:

- official-style task is "Multiple answers might be correct"
- several management steps are simultaneously correct
- several imaging findings or complications are correct
- several risk factors/features are being tested
- the answer page clearly lists a set of correct statements

Choice question quality rules:

- Use exactly 5 options unless preserving a source-verbatim official item with a different count.
- Remove `a.`, `b.`, `Both a and b`, `None of the above`, and similar exam artefacts unless they are intentionally retained from a source item.
- Avoid very long options.
- Do not make options depend on source wording rather than clinical reasoning.

---

## Question Count Guidance

Target most cases at 4-6 questions.

- 3 questions is acceptable for a sparse case.
- 7-8 questions usually feels too textbook-like unless the official source case genuinely has that many steps.
- If a case has too many questions, mark candidates for later pruning, but do not delete questions without explicit approval.

Suggested distribution per case:

- 1-2 free-text imaging/finding questions
- 1 additional free-text reasoning question chosen from diagnosis, differential diagnosis, management, complications, staging/classification, or report recommendation when suitable
- 1-2 choice questions for management, staging, complications, or teaching points

Across a batch, do not always convert the same question position or the same reasoning step.

Later free-text balance validation:

- Count only Q3+ `free_text` questions. Exclude Q1/Q2 findings from the calculation.
- Assign each Q3+ `free_text` question to exactly one family: `diagnostic_reasoning`, `management`, or `complication_teaching`.
- Calculate percentages as: `family_count / total_later_free_text_questions * 100`.
- Target: 33% per family.
- Passing range: each family must be 30-35%, unless the source genuinely cannot support it.
- If any family is outside 30-35%, revise the batch before insertion/repair.
- For very small batches, use nearest practical rounding but still report percentages.
- Direct diagnosis free text counts under `diagnostic_reasoning`.

Required validation summary:

```text
Later free-text distribution:
- diagnostic_reasoning: 34%
- management: 32%
- complication_teaching: 34%
Validation: pass
```

If the source forces an exception, document it:

```text
Validation exception:
- failing family:
- observed percentage:
- reason source cannot support target balance:
- affected case numbers:
```

---

## Answer Page Review Process

For each case:

1. Read current DB content:
   - case vignette
   - every question
   - q_type, options, correct_options
   - answer_text and explanation
   - question and answer page images

2. Inspect original answer page images or attached answer pages:
   - identify the actual diagnosis
   - identify the findings the source expects
   - identify differential diagnosis lists
   - identify management recommendations
   - identify complications, staging, classifications, or report recommendations
   - identify marking criteria or partial-credit alternatives

3. Decide edits:
   - keep, convert, rewrite stem, repeat images, or flag for image repair
   - prefer 1-2 conversions per case
   - do not over-polish stable content

4. Apply changes transactionally:
   - back up DB first
   - update only selected rows
   - roll back on failure

5. Verify:
   - no invalid q_type
   - free_text has `options = NULL` and `correct_options = NULL`
   - single_choice has exactly one `answer_text` and no `correct_options`
   - multiple_choice has `correct_options` and empty/NULL `answer_text`
   - options JSON is valid
   - image paths exist

---

## Rewrite Rules

Replace generated wording:

- `Which source-supported statements are correct?`
- `Which statements are source-supported after diagnosis?`
- `Which entities belong in the source differential?`
- `Which differential features are source-supported?`

With exam-style wording:

- `Which statements are correct?`
- `Which differential diagnoses should be considered?`
- `Which features support this diagnosis?`
- `Which imaging features favour this diagnosis?`
- `Which complications should be considered?`

Avoid revealing the diagnosis too early.

- If Q1 asks for findings, do not mention the final diagnosis in the stem.
- If a later question reveals biopsy or final pathology, make that reveal explicit in the stem.

Examples:

```text
Before:
Which source-supported statements are correct after this diagnosis has been made?

After:
Which statements about this diagnosis are correct?
```

```text
Before:
Which entities belong in the source differential for this imaging appearance?

After:
What are the two most likely differential diagnoses?
```

---

## Image Assignment Rules

Official CORE questions commonly keep relevant images visible on multiple questions. Therefore:

- Q1/Q2 findings questions should show the relevant images.
- Diagnosis and differential questions may repeat the same images if the user needs them to answer.
- Later management/teaching questions may omit images if they depend only on the established diagnosis.
- If answer images show annotated findings, keep them in `answers.page_images`.

If image labels/captions are available from the source, preserve them in question text or future metadata. Current DB image paths do not support captions directly.

---

## Batch Workflow

Work one source/chapter at a time.

Recommended order:

1. `FRCR Long Cases v1.1`
2. `FRCR Long Cases v2`
3. `Radcases`

For each batch:

1. Create a timestamped backup:
   - `data/edir_prep.db`
   - any crop files modified in the batch

2. Generate an audit table:
   - source
   - chapter
   - case_id
   - case_number
   - current q_type distribution
   - candidate conversions
   - image issues
   - proposed changes

3. Review the proposed changes before large-scale mutation when the batch is broad.

4. Run one transactional repair script.

5. Produce a concise change log:
   - changed case/question IDs
   - old q_type -> new q_type
   - old stem -> new stem when changed
   - answer conversion notes
   - any image path changes

---

## Audit Output Format

Use this format before applying a batch:

```text
Source: FRCR Long Cases v1.1
Chapter: Genitourinary Radiology

Case 135 / case_number 2
- Keep Q1 free_text findings.
- Keep Q2 free_text additional findings.
- Keep Q3 single_choice diagnosis because the options test close mimics.
- Convert Q4 multiple_choice -> free_text differential diagnosis.
- Keep Q5 single_choice management.
- Repeat Q1/Q2 image paths on Q3 because diagnosis depends on the images.
- Repeat Q1/Q2 image paths on Q4 because differential diagnosis depends on the images.

Reason:
The diagnosis options are educational, but the answer page gives a short markable differential list. Management remains a good single-best-answer item.
```

After applying:

```text
Changed:
- case 135 Q4: multiple_choice -> free_text
- stem: "Which differential diagnoses should be considered?" -> "What are the two most likely differential diagnoses?"
- answer_text: "Endometrioma\nMature cystic teratoma"
- options/correct_options cleared
- page_images copied from Q2 because the question depends on the images
```

---

## Hard Stops

Stop and ask before continuing if:

- the answer page contradicts the current DB answer
- the diagnosis is unclear
- image assignment is ambiguous and would change the case meaning
- a batch would require deleting questions
- source pages are missing or unreadable

Do not stop for minor wording choices; make a conservative edit and log it.
