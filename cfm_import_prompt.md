# UEFA CFM MRQ Generation and Import Prompt

Use this workflow only for the ten PDFs from the UEFA *Handbook of Football
Association Management*. It generates new study questions from teaching text;
it does not extract pre-existing questions.

## Fixed course structure

All output belongs to:

- library: `uefa_cfm`
- database chapter number: `15`
- database chapter title: `UEFA Certificate in Football Management`
- section: `mrq`
- one PDF = one complete MRQ session

Process sources in handbook order:

1. `UEFA-HFM-The-organisation-of-world-football.pdf` - Chapter 1: The organisation of world football
2. `Strategic-Management.pdf` - Chapter 2: Strategic management
3. `Operational-management.pdf` - Chapter 3: Operational management
4. `UEFA-HFM-Football-Marketing.pdf` - Chapter 4: Football marketing
5. `Communication-the-media-and-public-relations.pdf` - Chapter 5: Communication, the media and public relations
6. `Event-and-volunteer.pdf` - Chapter 6: Event and volunteer management
7. `UEFA-HFM-Football-and-social-responsibility.pdf` - Chapter 7: Football and social responsibility
8. `UEFA-HFM-Womens-football.pdf` - Chapter 8: Women's football
9. `UEFA-HFM-Football-Development.pdf` - Chapter 9: Football development
10. `UEFA-HFM-Football-law.pdf` - Chapter 10: Football law

Chapter 7 has corrupt embedded text encoding. Render every page and read it
visually or with OCR; do not generate from its broken extracted character stream.

## Mandatory per-PDF cycle

Never generate or import more than one PDF at a time.

1. Read the complete PDF, including diagrams and tables, but exclude spill-over
   references belonging to the preceding chapter.
2. Inventory its headings, frameworks, processes, comparisons, examples,
   governance rules, decision criteria, and practically examinable facts.
3. Record printed handbook page numbers and their corresponding 1-based PDF
   pages. A landscape PDF page may contain two printed handbook pages.
4. Create a blueprint of 80-120 non-overlapping questions. Aim near 100, but
   stop before introducing repetition, trivial details, or unsupported claims.
5. Draft and validate the entire staged JSON session.
6. Run `py -3.13 -m core.cfm_import <json> <pdf>` without the import flag.
7. Present the validation audit and a representative sample to the user.
8. Stop. Import only after explicit approval by rerunning with
   `--import-approved`. Complete that import before starting the next PDF.

## Educational target

The questions prepare a learner for an oral examination while retaining the
app's multiple-response interaction.

Across each session, target approximately:

- 45% applied scenarios: choose or assess actions in a realistic football
  association situation;
- 35% explanation, comparison, prioritisation, or justification of concepts;
- 20% high-yield factual anchors, named frameworks, roles, or process steps.

Prefer prompts that test whether the learner can explain why a course of action
fits the situation. Avoid author names, affiliations, reference lists, URLs,
publication trivia, decorative examples, and isolated numbers with no management
significance.

The supplied PDF is the only authority. Do not browse for updates or silently
replace handbook claims with current information. Every correct statement,
distractor, and explanation must be defensible from the cited source pages.

## MRQ rules

- English, using the handbook's terminology and British spelling.
- Every item is standalone and uses a positive stem.
- `q_type` is always `multiple_choice`.
- Exactly five concise, parallel, plausible options.
- One to four correct options; never zero or five.
- Use 0-based `correct_options` indices.
- Mix one-, two-, three-, and four-answer questions. No answer count may exceed
  55% of a session.
- Spread correct answers across positions a-e; each position should be correct
  in 30-70% of questions.
- Do not use `all of the above`, `none of the above`, joke options, obvious
  opposites, grammatical clues, or longer-is-correct patterns.
- Incorrect statements must be adjacent, plausible misconceptions that can be
  corrected from the same cited material.
- Do not create near-duplicate stems that test the same decision from cosmetic
  wording changes.

### Distractor quality standard

Wrong options must be credible to a partially prepared candidate. They should
fail because of one precise error in scope, responsibility, sequence, timing,
priority, causal logic, or interpretation of a neighbouring concept in the same
cited passage. Prefer, for example:

- assigning a real responsibility to the wrong but related governing body;
- applying a valid principle at the wrong organisational level or stage;
- confusing two adjacent framework elements or reversing their relationship;
- choosing a plausible action that is premature, incomplete, or misprioritised;
- using a source-grounded detail with subtly incorrect scope or justification.

Do not make an option false by using giveaway absolutes such as `all`, `always`,
`never`, `only`, `every`, `entirely`, `automatically`, `guaranteed`,
`permanent`, `impossible`, `identical`, `exclusively`, or `regardless`. Avoid
absurd category errors, invented powers that are obviously unrelated to the
stem, joke-like wording, and extreme claims about abolition, immunity,
prohibition, or elimination. Keep distractors similar to correct options in
length, specificity, tone, and grammatical form.

For each distractor, ask: could a candidate with incomplete but genuine course
knowledge defend this option for several seconds? If the answer is no, rewrite
it. Then state privately which exact source-supported distinction makes it
wrong; if that distinction cannot be identified, reject the option.

## Model oral answer

Each answer explanation must be a concise spoken-style model answer, normally
3-6 sentences. It should:

1. state the governing concept or framework;
2. apply or justify it in relation to the stem;
3. distinguish the principal misconception or distractor;
4. avoid referring to options only by letters.

The app renders the structured source citation separately, so do not repeat a
long citation inside the explanation.

## Key diagrams and tables

Use a crop only when the visual structure itself is worth recalling, such as a
named framework, flow, matrix, or compact comparison table. Do not include
photographs, branding, decorative graphics, dense prose pages, or any crop that
reveals the answer verbatim.

Crop coordinates are fractions of the complete landscape PDF page:

```json
{
  "pdf_page": 6,
  "bbox": {"left": 0.05, "top": 0.15, "right": 0.48, "bottom": 0.78},
  "caption": "Core elements of England's footballing DNA"
}
```

Visually inspect every rendered crop before approval.

## Staged JSON schema

Save approved-quality staging artifacts under `data/cfm_imports/` using stable
filenames such as `chapter_01_organisation_of_world_football.json`.

```json
{
  "schema_version": 1,
  "library_key": "uefa_cfm",
  "chapter_number": 15,
  "session_title": "Chapter 1 - The organisation of world football",
  "source_pdf": "UEFA-HFM-The-organisation-of-world-football.pdf",
  "questions": [
    {
      "q_number": 1,
      "question_text": "Which statements correctly describe ...?",
      "q_type": "multiple_choice",
      "oral_exam_category": "application",
      "options": ["...", "...", "...", "...", "..."],
      "source_locator": {
        "file": "UEFA-HFM-The-organisation-of-world-football.pdf",
        "pdf_pages": [2],
        "handbook_pages": [14, 15]
      },
      "page_crops": [],
      "answer": {
        "correct_options": [0, 2],
        "explanation": "A concise model oral answer of at least three sentences."
      }
    }
  ]
}
```

`oral_exam_category` is required and must be `application`, `explanation`, or
`factual_anchor`. The validator enforces a tight tolerance around the planned
45% / 35% / 20% blueprint (40-50% / 30-40% / 15-25%).

## Hard validation before approval

- One session object and 80-120 consecutive questions.
- Auditable oral-exam categories within the planned blueprint tolerance.
- Exact PDF filename and valid 1-based PDF pages on every question.
- Non-empty printed handbook pages on every question.
- Five distinct options and one to four valid answer indices per question.
- Balanced answer counts and answer positions.
- Zero distractors containing giveaway absolutes or implausible category errors;
  manually review semantic plausibility even when the lexical check passes.
- No unsupported, ambiguous, redundant, negative-stem, or trivia-only items.
- No near-duplicate stems or repeated option sets.
- Every model oral answer is source-grounded and resolves the main distractor.
- Every crop has a valid normalized box, useful caption, clean rendering, and no
  answer leakage.
- Validation CLI returns `"valid": true` before the audit is shown for approval.
