# Reporting Systems (RADS/Grading) MRQ Import — Prompt & Workflow Reference

*Companion to `import_prompts.md`. Read that file's **"MRQ Prompt"** section first (options count,
`correct_options` format, explanation style, correct-answer distribution/blueprint checkpoint,
distractor quality rules, anti-hallucination rules, per-batch cycle) — every rule there applies here
unless explicitly overridden below. This document only covers what's specific to this import.*

---

## Source files

All source documents live in two folders (already downloaded, verified as valid PDFs/MD files):

- `C:\Users\Razvan\Documents\Radiologie\EDiR\Reporting Systems (RADS)\`
- `C:\Users\Razvan\Documents\Radiologie\EDiR\Trauma Imaging Guidelines\`

Two files are Markdown (`VI-RADS_TeachingSummary_RadiologyAssistant.md`,
`Bosniak_2019_TeachingSummary_RadiologyAssistant.md`) — read them as plain text, no PDF extraction needed.
Everything else is a PDF — use PyMuPDF (`fitz`) text extraction as with any other book import.

---

## DB source label and section

- Every case generated from this import uses **`"source": "Reporting Systems"`** (new source label —
  does not exist in the DB yet, this import creates it).
- Every case uses **`"section": "mrq"`**.
- `"library_key": "edir"` (default — do not change).
- Put the system's full name (e.g. `"LI-RADS v2018 (CT/MRI)"`, `"Bosniak Classification (2019)"`) in
  `clinical_vignette`, exactly like the Scientific Articles convention, so each MRQ session is
  identifiable in the case list.
- Omit `original_answer_pages` — these are guideline documents, not case books with discrete answer
  pages.
- `article_summary`: **required for every case in this import.** Follow the Scientific Articles format
  (metadata block, then structured sections) with one addition specific to this import — a **category
  cheat-sheet** (see below). This is the user's explicit request: they want a simple, short definition of
  every category (e.g. what LI-RADS 1 means, what LI-RADS 3 means, etc.), not just the MRQ questions.

### Article summary format for this import

Use this structure (adapt section names to fit the system, but always include the cheat-sheet):

- `### <System name>`
- `**Source:** <document title, publisher/society, year/version>`
- `**Scope:** <one line — what this system is used for and on which modality/modalities>`
- `### Category cheat-sheet` — **the core deliverable the user asked for.** One line per category, plain
  language, no jargon beyond what a resident already knows. Format as a table or tight bullet list:
  `**LR-1 — Definitely benign:** <one short plain-language sentence, e.g. typical benign lesion, no
  follow-up beyond routine surveillance>`. Do this for **every** category in the system, not just the ones
  used as Template C options in the MRQs — this is a standalone quick-reference the learner will scan
  independently of the questions. Keep each line to one sentence; this is a cheat-sheet, not a restatement
  of the full diagnostic criteria table.
- `### Key imaging/scoring points` — the non-category-specific technical content: how to score, sequence/
  timing requirements, tie-breaker rules, ancillary features, upgrade/downgrade rules.
- `### Practical/management implications` — what each category (or category range) actually changes in
  patient management/follow-up, kept brief; this can cross-reference the cheat-sheet rather than repeat it.
- `### Pitfalls and limitations` — mimics, common scoring errors, stated limitations of the system.
- `### Take-home points` — 3-5 bullets.

Length: the cheat-sheet itself should stay compact (one line per category); the rest of the summary should
follow the Scientific Articles length guidance (roughly 700-1200 words total for the whole `article_summary`,
cheat-sheet included) — do not let it balloon into a restatement of the entire source document.

For the two split topics (RECIST, NODE-RADS), each of the smaller per-chapter cases still gets its own full
`article_summary` including the complete cheat-sheet (e.g. all 4 RECIST response categories), even though
that case's MRQs only cover a subset of scenarios — the cheat-sheet is reference material, not scoped to
that case's specific questions.

---

## Target: 20-30 MRQs per reporting system

This overrides the density-scaling rule used for Scientific Articles (which targets 4-12 MRQs based on
article length). These are dense, structured, high-yield documents — aim for the full 20-30 per system
regardless of document length, same target used for dense MRQ sources elsewhere in `import_prompts.md`
(e.g. BI-RADS-style dense classification content). Never pad past what the source actually supports, but
these documents are dense enough that 20-30 should be achievable for every system without padding.

---

## Question format mix (new: Template C)

Reuse `import_prompts.md`'s **Template A** (image-based) and **Template B** (knowledge) `multiple_choice`
formats for most of each set. In addition, use a new **Template C** for this import only:

**Template C — Classification scenario (`single_choice`)**
> "\<Clinical/imaging vignette describing a lesion or finding, written the way an exam stem would —
> patient context if relevant, modality, and the specific descriptive findings needed to score it\>.
>
> What is the most appropriate \<system\> category for this finding?"

- `q_type`: `"single_choice"`.
- `options`: exactly 5 — the plausible category set for that system (see per-system category lists
  below). If a system has more than 5 categories (e.g. CAD-RADS 0-5 is 6 categories, Bosniak has 5
  including IIF), pick the 5 most discriminating/testable options for that specific vignette rather than
  omitting a category system-wide — vary which categories are tested across the batch so all real
  categories appear somewhere in the set of Template C questions for that system.
- `answer_text` = the correct option's exact text; `correct_options` = `null` (standard `single_choice`
  format).
- The vignette must give **enough scoring detail to uniquely determine the category** per the source's
  own criteria — size thresholds, enhancement pattern, washout, capsule, threshold growth, morphology
  descriptors, whatever the source uses to define that category. Do not write an ambiguous vignette that
  could plausibly fit two categories.
- Explanation: state which specific criterion/criteria drove the category assignment, and briefly why the
  nearest distractor category doesn't fit (without referencing options by letter).

**Mix ratio per system:** roughly 60-70% Template A/B (`multiple_choice` statement-verification) and
30-40% Template C (`single_choice` classification scenarios). For a 24-question set this is about
15-16 Template A/B and 8-9 Template C. Write the blueprint checkpoint (per `import_prompts.md`) covering
**both** the `multiple_choice` correct-count/position distribution AND how many Template C questions are
planned and which categories they'll cover, before drafting options.

The `multiple_choice`→`single_choice` split does not change the `multiple_choice` correct-answer-count/
position distribution rules from `import_prompts.md` — apply those to the Template A/B subset only.
Template C questions are not counted toward that distribution (they use `correct_options: null` like any
other `single_choice` question).

---

## Images

These are official atlases/guidelines and frequently contain real illustrative CT/MRI/US example images
tied to specific categories (e.g. the PI-RADS and LI-RADS ACR manuals, BI-RADS lexicon forms, TI-RADS
atlas). **Prefer building Template C questions around these real illustrative images when the source
provides them** — this is far more authentic than a pure-text vignette and is exactly the kind of "select
the category" question the user asked for.

- Extract and crop illustrative example images the same way as any other book import: PyMuPDF, `>= 200px`
  clinical-image filter, visual inspection before finalizing which image maps to which category, `data/
  crops/` path prefix (see the master schema rule in `import_prompts.md` — bare filenames are silently
  ignored by the app).
- Skip schematic/diagram-only figures with no real patient imaging (pure line-drawing algorithms, decision
  trees, anatomic schematics) — those aren't useful as an "identify the category from the image" question,
  though they may still support a text-based Template A/B question about the algorithm itself.
  Diagrams reproducing the actual grading/scoring criteria table (e.g. a table of Agatston score ranges,
  a BI-RADS category table) are fine to use as reference while *writing* the question — just don't attach
  the table itself as a `page_images` entry.
  When several categories share one obvious composite/reference figure (e.g. a single figure showing all
  5 PI-RADS categories side by side), only use that composite for a general text-based multiple_choice
  question, not for a single-category Template C question — it would leak the answer alongside the other
  four categories that were not asked about.
- If no suitable real example image exists for a category, write the Template C question as pure text
  instead. Do not fabricate or misattribute an image.
- Do not use ACR/society logos, cover pages, or decorative headers.

---

## Distractor quality (Template C specific)

- The 5 category options for a given vignette should span a **plausible, closely-related range** on the
  same scale (e.g. don't pair "LR-1 (definitely benign)" against "LR-5 (definitely HCC)" as the only two
  meaningful options with 3 throwaway distractors — include adjacent categories like LR-3/LR-4/LR-M so the
  learner has to apply the actual size/enhancement/washout thresholds, not just pattern-match "sounds
  aggressive vs sounds benign").
- Reuse the general distractor-quality rules from `import_prompts.md`: no giveaway absolutes, no
  unrelated-organ distractors, every option must be a real category from that same system.

---

## Per-system source file, target chapter(s), and case-count plan

Process **one topic per batch**, per the Mandatory Per-Batch Cycle in `import_prompts.md`. Each row below
is one *topic*; some topics split into more than one DB case (see "Cases" column) — when a topic splits,
divide the 20-30 total MRQs across its cases roughly evenly, and cover the cross-cutting/general-principle
content across the split cases rather than dumping it all into one.

| # | Topic | Source file(s) | DB chapter(s) | Cases | Category options for Template C |
|---|---|---|---|---|---|
| 1 | RECIST 1.1 | `RECIST_1.1_2009_EORTC.pdf` | Split: **Chest and Thorax Radiology** (pulmonary/mediastinal target-lesion scenarios) + **Abdominal Radiology** (hepatic/nodal target-lesion scenarios, plus all organ-agnostic general-principle content — measurability rules, target/non-target selection, CR/PR/SD/PD definitions, new-lesion rules — default here since liver is the classic RECIST teaching organ) | 2 cases, ~10-15 MRQs each | Response categories: Complete Response, Partial Response, Stable Disease, Progressive Disease (+ "Not evaluable" as a distractor where relevant) |
| 2 | LI-RADS | `LI-RADS_CTMRI_v2018_Full_Manual_ACR.pdf` (primary), `LI-RADS_Lexicon_2021_ACR.pdf`, `LI-RADS_US_Surveillance_v2024_ACR.pdf`, `LI-RADS_CEUS_v2017_ACR.pdf` | Abdominal Radiology | 1 case, 20-30 MRQs | LR-1, LR-2, LR-3, LR-4, LR-5, LR-M, LR-TIV (pick 5 most relevant per vignette) |
| 3 | Lung-RADS | `Lung-RADS_v2022_ACR.pdf` | Chest and Thorax Radiology | 1 case, 20-30 MRQs | Lung-RADS 0, 1, 2, 3, 4A, 4B, 4X (pick 5 per vignette) |
| 4 | PI-RADS v2.1 | `PI-RADS_v2.1_2019_ACR_ESUR.pdf` | Genitourinary Radiology | 1 case, 20-30 MRQs | PI-RADS 1, 2, 3, 4, 5 |
| 5 | BI-RADS | `BI-RADS_v2025_Lexicon_Summary_Mammography_ACR.pdf`, `..._Ultrasound_ACR.pdf`, `..._MRI_ACR.pdf` | Breast Radiology | 1 case, 20-30 MRQs (mix mammography/US/MRI scenarios) | BI-RADS 0, 1, 2, 3, 4 (4A/4B/4C acceptable as sub-options), 5, 6 (pick 5 per vignette) |
| 6 | O-RADS | `O-RADS_US_v2022_ACR.pdf`, `O-RADS_MRI_2020_ACR.pdf` | Genitourinary Radiology | 1 case, 20-30 MRQs (mix US/MRI scenarios) | O-RADS 1, 2, 3, 4, 5 |
| 7 | NODE-RADS | `NODE-RADS_2021_EurRadiol.pdf` | Split three ways: **Head and Neck** (cervical nodal scenarios), **Chest and Thorax Radiology** (mediastinal/hilar nodal scenarios), **Abdominal Radiology** (abdominopelvic/retroperitoneal nodal scenarios) | 3 cases, ~7-10 MRQs each; distribute the general morphological-criteria content (size, shape, necrosis, extranodal extension) evenly across all three rather than concentrating it in one | NODE-RADS 1, 2, 3, 4, 5 |
| 8 | TI-RADS (ACR) | `TI-RADS_Atlas_ACR.pdf` | Head and Neck | 1 case, 20-30 MRQs | TR1, TR2, TR3, TR4, TR5 |
| 9 | NI-RADS | `NI-RADS_Atlas_2025_ACR.pdf` | Head and Neck | 1 case, 20-30 MRQs | NI-RADS 1, 2, 3, 4 (primary and nodal — vary which is tested) |
| 10 | C-RADS | `C-RADS_v2023_ACR.pdf` | Abdominal Radiology | 1 case, 20-30 MRQs | Colonic: C0, C1, C2a, C2b, C3, C4 (6 real tiers — the 2023 update splits C2 into C2a/C2b); Extracolonic: E1/E2 (merged), E3, E4 (the 2023 update merges E1 and E2 into one tier and does **not** define an E0 tier — confirmed against the actual downloaded PDF, corrected here from an earlier incorrect assumption of E0-E4) |
| 11 | CAD-RADS 2.0 | `CAD-RADS_2.0_2022.pdf` | Cardiac Radiology | 1 case, 20-30 MRQs | CAD-RADS 0, 1, 2, 3, 4, 5 (pick 5 per vignette; also test modifiers N/S/G/I/HRP in Template A/B, not as Template C categories) |
| 12 | VI-RADS | `VI-RADS_TeachingSummary_RadiologyAssistant.md` | Genitourinary Radiology | 1 case, 20-30 MRQs | VI-RADS 1, 2, 3, 4, 5 |
| 13 | Bosniak (2019) | `Bosniak_2019_TeachingSummary_RadiologyAssistant.md` | Genitourinary Radiology | 1 case, 20-30 MRQs | Bosniak I, II, IIF, III, IV |
| 14 | Agatston / CAC scoring | `Agatston_CAC_Scoring_SCCT-STR_Guidelines_2016.pdf` | Cardiac Radiology | 1 case, 20-30 MRQs | Score-range risk categories: 0 (none), 1-99 (minimal), 100-399 (moderate), \u2265400 (severe) \u2014 use as the Template C "category" scale in place of a lettered system |
| 15 | Liver trauma grading | `Liver_Trauma_WSES_2020_incl_AAST-OIS_grading.pdf` | Abdominal Radiology | 1 case, 20-30 MRQs | AAST-OIS Grade I, II, III, IV, V (use the 2018 revision criteria as reproduced in the WSES document) |
| 16 | Splenic trauma grading | `Splenic_Trauma_WSES_2017_Guidelines_incl_AAST-OIS_grading.pdf` (primary), `Splenic_Trauma_WSES_2022_Followup_NOM_Consensus.pdf` (secondary, for non-operative-management follow-up content) | Abdominal Radiology | 1 case, 20-30 MRQs | AAST-OIS Grade I, II, III, IV, V |
| 17 | Kidney/urotrauma grading | `Kidney_Urotrauma_WSES-AAST_2019_Guidelines_incl_AAST-OIS_grading.pdf` | Genitourinary Radiology | 1 case, 20-30 MRQs | AAST-OIS Grade I, II, III, IV, V |

**Total: 20 DB cases across 17 topics, roughly 400-600 MRQs.** This is large — process strictly one case
at a time per the Mandatory Per-Batch Cycle, not one topic's entire multi-case split in a single pass.

---

## Chapter ID reference

Re-run this at the start of the import session (chapter IDs may drift if the chapters table changes):

```python
from core.database import get_chapters
chapters = get_chapters()
for ch in chapters:
    print(ch["id"], ch["number"], ch["title"])
```

At time of writing: Abdominal Radiology=1, Breast Radiology=2, Cardiac Radiology=3,
Chest and Thorax Radiology=4, Genitourinary Radiology=5, Head and Neck=6,
Interventional and Vascular Radiology=7, Musculoskeletal Radiology=8, Neuroradiology=9,
Pediatric Radiology=10.

---

## MRQ generation focus (reuse Scientific Articles judgment, adapted)

Apply the same "would this help me report, protocol, choose imaging, avoid an interpretive pitfall, or
discuss management/follow-up?" filter used for Scientific Articles imports. Specifically prioritise:

- The exact category-defining criteria (size thresholds, enhancement/washout rules, morphology
  descriptors, growth thresholds) — this is the highest-yield content and the natural Template C source.
- Modality-specific technical requirements (protocol, sequences, timing) where the source is prescriptive.
- Management/follow-up implications tied to each category (e.g. LR-3 surveillance interval vs LR-5 no
  biopsy needed; PI-RADS 3 vs 4 biopsy threshold; Bosniak IIF follow-up vs III/IV surgical
  consideration; AAST grade thresholds for non-operative management).
- Common pitfalls, mimics, and upgrade/downgrade rules explicitly stated by the source (e.g. LI-RADS
  ancillary features, threshold growth, ductal invasion; ACR's category-selection tie-breaker rules).
- Do not ask about document authorship, committee membership, publication history, or revision-process
  trivia — these are official guidelines, not journal articles, but the same "durable clinical knowledge,
  not journal-club trivia" principle applies.
- Do not use document-referential wording in visible stems ("according to this guideline", "the ACR
  states", "per this document") — phrase everything as durable exam-style radiology knowledge, exactly as
  the Scientific Articles rule requires.

**Style:** British English clinical register, ST4-ST7/fellow level. Every option, category assignment, and
explanation must be grounded in the source document — do not import outside knowledge of these systems
that isn't actually in the downloaded PDF/MD, even if it's true (a newer/older edition may define a
threshold differently).

---

## Validation before insertion (per case)

- `"source"` is exactly `"Reporting Systems"`, `"section"` is `"mrq"`.
- Chapter routing matches the table above (or a documented split for RECIST/NODE-RADS).
- Question count is 20-30 for a non-split topic, or the case's fair share of 20-30 for a split topic.
- Template A/B vs Template C ratio is roughly 60-70/30-40.
- Template C vignettes are unambiguous (map cleanly to exactly one category under the source's own
  criteria) and options are 5 plausible same-scale categories, not an arbitrary mix.
- Template C category coverage: across all Template C questions in a case, check that most/all real
  categories for that system appear as the *correct* answer somewhere in the set, not just the two most
  "obviously different" ends of the scale.
- `multiple_choice` correct-count and a-e position distribution follows the general MRQ rules, calculated
  over the Template A/B subset only.
- Images (where used) are real illustrative source figures, correctly mapped, `data/crops/`-prefixed, and
  not answer-leaking composites.
- No document-referential wording in visible stems/options/explanations.
- `clinical_vignette` contains the full system name.
- `article_summary` is present for every case, follows the format above, and its category cheat-sheet
  covers **every** category in that system (not just the ones tested in Template C), in short plain-language
  one-liners.
