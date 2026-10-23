"""Stage, validate, and transactionally improve EDiR SC/CORE distractors.

Scope: EDiR cases in the ``sc`` and ``core`` sections, excluding the
``Essential Guide`` source. Free-text questions and negative-stem questions are
audited but not rewritten. Source-native option counts are preserved.

Usage:
    python tools/upgrade_sc_core_distractors.py stage
    python tools/upgrade_sc_core_distractors.py validate
    python tools/upgrade_sc_core_distractors.py apply
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "edir_prep.db"
STAGE_DIR = ROOT / "data" / "sc_core_distractor_upgrade"
STAGE_FILE = STAGE_DIR / "sc_core_distractor_upgrade.json"
AUDIT_FILE = STAGE_DIR / "sc_core_distractor_upgrade_audit.json"
SOURCE_REVIEW_FILE = STAGE_DIR / "sc_core_source_review.json"
SOURCE_PAGE_CACHE_FILE = ROOT / "tmp" / "pdfs" / "sc_core_source_page_cache.json"
BACKUP_DIR = Path(
    r"C:\Users\Razvan\Documents\Radiologie\backups\SC_CORE_distractor_upgrade"
)
SOURCE_PDF_DIR = Path(
    r"C:\Users\Razvan\Documents\Radiologie\EDiR\EDIR Materiale - Roman Alexandru"
    r"\EDIR Materiale - Roman Alexandru\Carti de cazuri - de facut dupa fiecare capitol"
)

# These mappings were verified by raster-correlating a stored Original Answer
# Page crop with the corresponding page of the source PDF (all correlations
# exceeded 0.99). The page number encoded in each crop name is zero-based.
SOURCE_PDFS = {
    "cases-in-radiology-oxford_body-mri-cases-cases-in-radiology_f485d3b7": "Body MRI Cases (Cases in Radiology).pdf",
    "cases-in-radiology-oxford_emergency-radiology-cases_db733788": "Emergency Radiology Cases.pdf",
    "cases-in-radiology-oxford_gastrointestinal-imaging-cases_d5b07e9e": "Gastrointestinal Imaging Cases.pdf",
    "cases-in-radiology-oxford_genitourinary-radiology-cases_a2ecea6c": "Genitourinary Radiology Cases.pdf",
    "cases-in-radiology-oxford_breast-imaging-cases-cases-in-radiology_db050384": "Breast Imaging Cases (Cases in Radiology).pdf",
    "cases-in-radiology-oxford_cardiac-imaging-cases_5665104a": "Cardiac Imaging Cases.pdf",
    "cases-in-radiology-oxford_chest-imaging-cases_204f0bb9": "Chest Imaging Cases.pdf",
    "cases-in-radiology-oxford_neuroradiology-cases_299f05fa": "Neuroradiology Cases.pdf",
    "cases-in-radiology-oxford_interventional-radiology-cases_655cff25": "Interventional Radiology Cases.pdf",
    "cases-in-radiology-oxford_musculoskeletal-imaging-cases_8d66a54e": "Musculoskeletal Imaging Cases.pdf",
    "cases-in-radiology-oxford_pediatric-imaging-cases-cases-in-radiology-ellen-c_274f9cb4": "Pediatric Imaging Cases (Cases in Radiology) -- Ellen Chung -- Cases in Radiolo.pdf",
    "frcr_long_cases_v1_1": "CORE1 cazuri scrise.pdf",
    "frcr_long_cases_v2": "CORE2 cazuri scrise.pdf",
    "radcases_thoracic": "(RadCases) Carlos S. Restrepo_ Steven M. Zangan - RadCases Plus Q&A Thoracic Imaging-Thieme (2021).pdf",
    "radcases_ultrasound": "(RadCases) Nami Azar (editor) - RadCases ultrasound imaging-Thieme (2015).pdf",
    "radcases_radcases-shailendra-chopra-radcases-genitourinary-_77da0caf": "(RadCases) Shailendra Chopra - Radcases genitourinary imaging-Thieme (2012).pdf",
    "radcases_re4b8-1_1c612833": "(RadCases) Stephen Thomas_ Jonathan M. Lorenz - RadCases Plus Q&A Gastrointestinal Imaging-Thieme (2020).pdf",
    "radcases_radcases-breast-imaging-radcases-plus-q-a-lonie-sa_1bdf4c83": "Radcases Breast Imaging (Radcases Plus Q&A) -- Lonie Salkowski, Jonathan Lorenz, He.pdf",
    "radcases_cardiac": "(RadCases) Carlos S Restrepo, Dianna M. E. Bardo - Cardiac Imaging-Thieme (2010).pdf",
    "radcases_radca-1_e3da88dc": "[RadCases] Choi, Jeanie M._ Friedman, Elliot R._ Shah, Gaurang_ Wesolowski, - RadCases head and neck imaging (2016, Thieme) - libgen.li.pdf",
    "radcases_msk": "(RadCases) Glenn M. Garcia - Radcases Musculoskeletal Radiology-Thieme (2017).pdf",
    "radcases_radcases-plus-q-a-neuro-imaging-susana-calle-edito_4c0fc675": "RadCases plus Q & A neuro imaging -- Susana Calle (editor); Eliana Bonfante (editor.pdf",
    "radcases_pediatric": "(RadCases) Richard B. Gunderman (editor), Lisa R. Delaney (editor) - Pediatric Imaging (RadCases)-Thieme (2010).pdf",
    "radcases_radcas-1_d83ba52f": "Radcases Breast Imaging (Radcases Plus Q&A) -- Lonie L_ Salkowski, Friedemann Baum, Uwe Fischer, Susanne -.pdf",
    "crack_case_companion": "(Crack the Core) Prometheus Lionhart M.D - Crack the core exam case companion (2015).pdf",
    "top3_differentials": "Top 3 Differentials in Radiology _ A Case Review -- William T_ O'Brien Sr_ -- 2nd ed, New York, 2018 -- Thieme Medical Publishers, Incorporated; -- isbn13 9781626232785 -- 2e7f0242b1b70455a60d46ded.pdf",
}

EXPECTED_CASES = 3196
EXPECTED_QUESTIONS = 15113
EXPECTED_SELECTABLE = 10872
EXPECTED_DISTRACTORS = 33333
EXCLUDED_SOURCE = "Essential Guide"


def _normalise(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def _json_hash(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _database_file_hash() -> str:
    digest = hashlib.sha256()
    with DB.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _correct_indices(
    options: list[str], correct_options: str | None, answer_text: str | None
) -> list[int]:
    if correct_options:
        try:
            parsed = json.loads(correct_options)
            return sorted({int(index) for index in parsed if 0 <= int(index) < len(options)})
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    answer = _normalise(answer_text)
    if answer:
        for index, option in enumerate(options):
            if _normalise(option) == answer:
                return [index]
    return []


NEGATIVE_STEM_RE = re.compile(
    r"(?:"
    r"\ball\s+of\s+the\s+following\b[^?]{0,180}\bexcept\b|"
    r"\b(?:which|what)\b[^?]{0,120}\b(?:is|are)\s+(?:false|incorrect|not\s+true)\b|"
    r"\b(?:which|what)\b[^?]{0,120}\b(?:does|do)\s+not\b|"
    r"\bleast\s+likely\b|"
    r"\bnot\s+(?:include|included|associated|considered|expected|typical|a\s+feature)\b"
    r")",
    re.IGNORECASE,
)


HIGH_GIVEAWAY_RE = re.compile(
    r"\b(?:always|never|cannot|every|none|impossible|guaranteed|identical|"
    r"exclusively|automatically|invariably|universally|ever)\b|\bunder\s+any\s+circumstances\b|"
    r"\b(?:in|for)\s+any\s+patients?\b|"
    r"(?<!nearly )(?<!almost )\ball\s+(?:patients?|cases?|lesions?|tumou?rs?|"
    r"findings?|studies|modalities|phases?|sequences?|views?|types?|forms?|subtypes?|"
    r"ages?|stages?|grades?|locations?|circumstances?)\b",
    re.IGNORECASE,
)

ONLY_RE = re.compile(r"(?<!-)\bonly\b", re.IGNORECASE)
WEAK_NO_RE = re.compile(
    r"(?:^|\b)(?:no\s+(?:treatment|follow-up|further|imaging|investigation|"
    r"management|intervention|action|therapy|surgery|biopsy|role|value|utility|risk|"
    r"association|relationship|connection|need|requirement|option|alternative|urgency|"
    r"monitoring|surveillance|referral|work-up|workup|enhancement\s+is\s+ever)|"
    r"has\s+no\s+(?:role|value|utility|risk|association|relationship|connection)|"
    r"have\s+no\s+(?:role|value|utility|risk|association|relationship|connection)|"
    r"requires?\s+no\s+(?:treatment|follow-up|further|additional|imaging|investigation|"
    r"management|intervention|action|therapy|surgery|biopsy|monitoring|surveillance))",
    re.IGNORECASE,
)


def is_negative_stem(text: str) -> bool:
    # Do not mistake terms such as "false-positive" or "false aneurysm" for a
    # negatively keyed question.
    scrubbed = re.sub(r"\bfalse[- ]positive\b|\bfalse\s+aneurysm\b", "", text)
    return bool(NEGATIVE_STEM_RE.search(scrubbed))


def has_weak_wording(text: str) -> bool:
    screened = re.sub(
        r"\b(?:nearly|almost)\s+always\b|\bevery\s+\d+(?:\.\d+)?\s*(?:days?|weeks?|months?|years?|hours?|minutes?)?\b",
        "",
        text,
        flags=re.IGNORECASE,
    )
    screened = re.sub(
        r"\bonly\s+(?:a\s+)?(?:tiny|small|minor|few)\s+(?:minority|proportion|number)?\b|"
        r"\bonly\s+\d+(?:\.\d+)?\s*(?:%|mm|cm|m|days?|weeks?|months?|years?|hours?)?\b",
        "",
        screened,
        flags=re.IGNORECASE,
    )
    return bool(
        HIGH_GIVEAWAY_RE.search(screened)
        or ONLY_RE.search(screened)
        or WEAK_NO_RE.search(screened)
    )


def _preserve_case(source: str, replacement: str) -> str:
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _word(text: str, source: str, replacement: str) -> str:
    return re.sub(
        rf"\b{re.escape(source)}\b",
        lambda match: _preserve_case(match.group(0), replacement),
        text,
        flags=re.IGNORECASE,
    )


def _replace_never_verb(match: re.Match) -> str:
    verb = match.group(1)
    lower = verb.casefold()
    irregular = {"has": "have", "does": "do", "is": "be"}
    if lower in irregular:
        return f"does not {irregular[lower]}"
    if lower.endswith("ies") and len(lower) > 3:
        return f"does not {verb[:-3]}y"
    if lower.endswith(("ches", "shes", "sses", "xes", "zes", "oes")):
        return f"does not {verb[:-2]}"
    if lower.endswith("s") and not lower.endswith("ss"):
        return f"does not {verb[:-1]}"
    return f"do not {verb}"


def rewrite_distractor(text: str) -> str:
    """Recast a weak option while retaining its original clinical proposition."""
    revised = text.strip()

    # Management and follow-up claims become realistic clinical alternatives.
    revised = re.sub(
        r"^No treatment because\s+(.+)$",
        r"Observation without active treatment is appropriate because \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No treatment(?:\s+is\s+(?:needed|required))?(?:\s+because)?\s*(.*)$",
        lambda match: "Observation without active treatment is appropriate"
        + (f" because {match.group(1)}" if match.group(1) else ""),
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No follow-up because\s+(.+)$",
        r"Clinical observation without interval imaging is appropriate because \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No follow-up(?:\s+is\s+(?:needed|required|recommended))?\s*(.*)$",
        lambda match: "Clinical observation without interval imaging is appropriate"
        + (f" {match.group(1)}" if match.group(1) else ""),
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno further (imaging|investigation|work-up|workup|management|treatment|action)\s+is\s+(?:needed|required)\b",
        r"additional \1 is unnecessary",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno further (imaging|investigation|work-up|workup|management|treatment|action)\b",
        r"without additional \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\brequires? no (imaging|investigation|treatment|follow-up|management|intervention|action|monitoring|surveillance)\b",
        r"can be managed without \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bhas no (role|value|utility)\b",
        r"has negligible \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bhave no (role|value|utility)\b",
        r"have negligible \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bhas no (association|relationship|connection) (?:with|to)\b",
        "is independent of",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bhave no (association|relationship|connection) (?:with|to)\b",
        "are independent of",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\b(?:needs?|requires?) no further (assessment|evaluation|consideration|testing|investigation|imaging|follow-up)\b",
        r"can be managed without further \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bneeds? no (intervention|monitoring|surveillance|follow-up)\b",
        r"can be managed without \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bneeds? no management\b",
        "is suitable for conservative observation",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\b(?:requiring|requires?|warrants?) no (?:further )?(assessment|evaluation|monitoring|surveillance|follow-up)\b",
        r"managed without further \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bhas no imaging overlap with\b",
        "is radiologically distinct from",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bhas no (treatment|management) implications\b",
        r"does not materially alter \1 planning",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bhas no management relevance\b",
        "does not materially affect management",
        revised,
        flags=re.IGNORECASE,
    )

    # "Cannot" becomes a specific limitation rather than a conspicuous absolute.
    revised = re.sub(
        r"\bcannot be (?:distinguished|differentiated) from\b",
        "is indistinguishable from",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(r"\bcannot be used for\b", "is unsuitable for", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bcannot be used\b", "is unsuitable", revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"\bcannot (?:reliably )?(distinguish|differentiate)\b",
        r"does not reliably \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bcannot (depict|detect|demonstrate|visualise|visualize|show)\b",
        r"is considered insensitive for demonstrating",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bcannot (assess|evaluate|quantify|characterise|characterize)\b",
        r"is considered unreliable for assessing",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(r"\bcannot cause\b", "is not a recognised cause of", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bcannot occur\b", "is not a recognised occurrence", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bcannot be missed\b", "is reliably detected", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bcannot\b", "does not", revised, flags=re.IGNORECASE)

    # Recast "never" in normal clinical negative language while preserving the
    # assertion. The verb inflection helper avoids malformed "does not has".
    revised = re.sub(r"\bis never\b", "is not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bare never\b", "are not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bwas never\b", "was not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bwere never\b", "were not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bhas never\b", "has not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bhave never\b", "have not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bcan never\b", "is unable to", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bwill never\b", "is not expected to", revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"^Never(?:,?\s+because)?\s*(.*)$",
        lambda match: "The proposed action is not indicated"
        + (f" because {match.group(1)}" if match.group(1) else " in this setting"),
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(r"\bnever\s+([A-Za-z-]+)", _replace_never_verb, revised, flags=re.IGNORECASE)

    # "Always" becomes a claimed defining or characteristic feature.
    revised = re.sub(
        r"^Always\s+([A-Za-z-]+)(.*)$",
        lambda match: f"{match.group(1).capitalize()}{match.group(2)} is the preferred approach",
        revised,
        flags=re.IGNORECASE,
    )
    revised = _word(revised, "always", "characteristically")
    revised = _word(revised, "invariably", "characteristically")
    revised = _word(revised, "universally", "generally")
    revised = re.sub(
        r"\b(can|could|may|will|would|should) ever\b",
        lambda match: match.group(1),
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bunder any circumstances\b",
        "despite a change in clinical circumstances",
        revised,
        flags=re.IGNORECASE,
    )

    # Population-wide assertions are expressed as absence of selection rather
    # than with conspicuous universal quantifiers.
    population_replacements = {
        r"\bin all patients\b": "without patient-specific selection",
        r"\bfor all patients\b": "without patient-specific selection",
        r"\ball patients\b": "patients irrespective of clinical context",
        r"\bin all cases\b": "irrespective of presentation",
        r"\bfor all cases\b": "irrespective of presentation",
        r"\ball cases\b": "cases irrespective of presentation",
        r"\ball lesions\b": "lesions irrespective of morphology",
        r"\ball tumours\b": "tumours irrespective of subtype",
        r"\ball tumors\b": "tumours irrespective of subtype",
        r"\ball findings\b": "findings irrespective of context",
        r"\ball phases\b": "arterial, portal venous, and delayed phases",
        r"\ball sequences\b": "the complete routine sequence set",
        r"\ball views\b": "the standard imaging views",
        r"\ball modalities\b": "the available imaging modalities",
        r"\ball types\b": "the full range of types",
        r"\ball forms\b": "the full range of forms",
        r"\ball subtypes\b": "the full range of subtypes",
        r"\ball stages\b": "the full disease spectrum",
        r"\ball grades\b": "the full grade spectrum",
        r"\ball ages\b": "the full age range",
        r"\ball circumstances\b": "irrespective of clinical circumstances",
    }
    for pattern, replacement in population_replacements.items():
        revised = re.sub(pattern, replacement, revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"\ball grade (\d+) ([^,.;]+?) (require|undergo|receive)s?\b",
        lambda match: f"Grade {match.group(1)} {match.group(2)} generally {match.group(3)}s",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\ball type ([A-Za-z0-9-]+) ([^,.;]+?) (require|undergo|receive)s?\b",
        lambda match: f"Type {match.group(1)} {match.group(2)} generally {match.group(3)}s",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\ball locations are equal in prevalence\b",
        "The principal locations have comparable prevalence",
        revised,
        flags=re.IGNORECASE,
    )

    every_replacements = {
        r"\bevery patient\b": "patients without clinical selection",
        r"\bevery case\b": "cases irrespective of presentation",
        r"\bevery lesion\b": "lesions irrespective of morphology",
        r"\bevery tumour\b": "tumours irrespective of subtype",
        r"\bevery tumor\b": "tumours irrespective of subtype",
        r"\bevery finding\b": "findings irrespective of context",
        r"\bevery study\b": "studies irrespective of indication",
        r"\bevery view\b": "the standard imaging views",
        r"\bevery phase\b": "each acquisition phase",
    }
    for pattern, replacement in every_replacements.items():
        revised = re.sub(pattern, replacement, revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"\ball grade (\d+) ([^,.;]+?)(?=\s+(?:require|undergo|receive|are|have)\b)",
        r"grade \1 \2 irrespective of associated findings",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\ball type ([A-Za-z0-9-]+) ([^,.;]+?)(?=\s+(?:require|undergo|receive|are|have)\b)",
        r"type \1 \2 irrespective of presentation",
        revised,
        flags=re.IGNORECASE,
    )
    revised = _word(revised, "every", "each relevant")
    revised = _word(revised, "every", "routine")

    # Remove redundant terminal "only" from diagnostic/management fragments;
    # elsewhere express the exclusive claim as a clinically plausible emphasis.
    revised = re.sub(r"\s+only(?=[.!?]?$)", "", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bonly after\b", "after", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bonly when\b", "when", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bonly in\b", "with a specific predilection for", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bonly for\b", "principally for", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bonly to\b", "principally to", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bonly by\b", "principally by", revised, flags=re.IGNORECASE)
    revised = _word(revised, "only", "principally")

    revised = re.sub(r"\bnone of the above\b", "the preceding alternatives are excluded", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bnone of these\b", "the listed alternatives are excluded", revised, flags=re.IGNORECASE)
    revised = _word(revised, "none", "neither group")
    revised = _word(revised, "identical", "indistinguishable")
    revised = _word(revised, "exclusively", "confined")
    revised = _word(revised, "automatically", "by itself")
    revised = _word(revised, "guaranteed", "regarded as definitive")
    revised = re.sub(r"\bmakes? ([^,.;]+?) impossible\b", r"excludes \1", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bis impossible\b", "is not considered feasible", revised, flags=re.IGNORECASE)
    revised = _word(revised, "impossible", "excluded")

    # Remaining targeted "no" constructions.
    revised = re.sub(
        r"^No further (assessment|evaluation|testing|investigation|imaging|follow-up|screening|surgery)(.*)$",
        lambda match: f"Further {match.group(1)} is unnecessary{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno further (assessment|evaluation|testing|investigation|imaging|follow-up) (?:is )?required\b",
        r"further \1 is unnecessary",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No (treatment|therapy|intervention|management)(.*)$",
        lambda match: f"Conservative management is appropriate{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No (imaging|investigation|testing|biopsy)(.*)$",
        lambda match: f"{match.group(1).capitalize()} is not indicated{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No (surveillance|monitoring)(.*)$",
        lambda match: f"Clinical observation without {match.group(1)} is appropriate{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\b(?:has|have) no risk of\b",
        "has a negligible risk of",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bthere is no risk of\b",
        "the risk is considered negligible for",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno (treatment|therapy|intervention|management) can\b",
        r"available \1 is unlikely to",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno imaging features\b",
        "nonspecific imaging features",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^Repeat no imaging because polyps is reliably detected$",
        "Repeat imaging is unnecessary because polyps are reliably detected",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno imaging follow-up\b",
        "clinical follow-up without interval imaging",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno need for\b",
        "limited value in",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No need to (.+)$",
        r"Limited value in attempting to \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno treatment is required\b",
        "conservative management is sufficient",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bsuggest no intervention\b",
        "suggest conservative observation",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No action if (.+)$",
        r"Accept the existing result if \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno management option is described\b",
        "the management approach is left unspecified",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No risk of (.+)$",
        r"The risk of \1 is considered negligible",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\brecommends? no treatment\b",
        "favours observation without active treatment",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\brequires? no further clinical evaluation\b",
        "can be managed without further clinical evaluation",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(r"^No ([^,.;]+?) is\b", r"\1 is not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"^No ([^,.;]+?) are\b", r"\1 are not", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bwith no\b", "without", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\band no\b", "without", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bno (role|value|utility)\b", r"negligible \1", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bno (association|relationship|connection)\b", r"independence", revised, flags=re.IGNORECASE)

    revised = re.sub(r"\s+", " ", revised).strip()
    if text[:1].isupper() and revised[:1].islower():
        revised = revised[:1].upper() + revised[1:]
    return revised


# The source banks use terse option fragments as well as complete sentences.
# Keep the final rewrite pass deliberately syntax-safe: modal phrasing works for
# singular and plural subjects, and calibrated frequency language preserves the
# original distractor's clinical proposition without conspicuous absolutes.
def rewrite_distractor(text: str) -> str:  # noqa: F811
    revised = text.strip()

    source_reviewed_short_forms = {
        "No intervention is ever required once stones are visible on MRCP": "Conservative observation is sufficient once stones are visible on MRCP",
        "No treatment is ever appropriate": "Supportive care is preferred to active treatment",
        "No treatment can improve function": "Available therapy is unlikely to improve function",
        "No treatment is ever considered": "Supportive care is the preferred approach",
        "No intervention is ever required if distal emboli have occurred": "Distal emboli can be managed conservatively",
        "No imaging is needed before removal": "Pre-removal imaging adds limited value",
        "No follow-up or treatment is ever needed": "Clinical observation without active treatment or scheduled follow-up is sufficient",
        "No imaging is useful before surgery": "Preoperative imaging adds limited value",
        "No treatment or follow-up is required": "Conservative observation without scheduled follow-up is sufficient",
        "No follow-up or repair": "Clinical observation without repair or scheduled follow-up is sufficient",
        "No need to assess chest wall relationship": "Assessment of the chest wall relationship has limited value",
        "Never, because this condition is always self-limited": "Conservative management is sufficient because this condition is self-limited",
        "Never, because tissue diagnosis is impossible": "Imaging is sufficiently specific to avoid tissue diagnosis",
        "Never, because imaging has no role": "Clinical assessment is sufficient without imaging",
        "Never in proximal vessel occlusion": "This approach is generally reserved for distal rather than proximal vessel occlusion",
        "Never, regardless of complications": "Complications do not alter the indication",
        "Never, because it is always asymptomatic": "Intervention is unnecessary in an asymptomatic presentation",
        "Never, regardless of clinical context": "Clinical context does not change the indication",
        "Never for haemorrhagic cysts": "Haemorrhagic cysts are managed without this intervention",
        "Never, even if symptomatic": "Symptoms alone do not justify the intervention",
        "Never enhances": "The lesion characteristically lacks enhancement",
        "Never pin, just relocate": "Relocation without pin fixation is preferred",
        "Never after lumpectomy": "Prior lumpectomy is a contraindication",
        "No therapy in all cases": "Supportive management is appropriate irrespective of presentation",
        "No therapy even if infected": "Supportive management remains appropriate despite infection",
        "Most thoracic imaging manifestations of leukemia are only seen on in children.": "Most thoracic imaging manifestations of leukemia are seen primarily in children.",
        "Repeat no imaging because polyps cannot be missed": "Repeat imaging is unnecessary because polyps are reliably detected",
        "Always no treatment or follow-up": "Conservative observation without scheduled follow-up is the standard approach",
        "Only change after surgery": "Postoperative change is the principal consideration",
        "Only phyllodes tumour is described as a sarcoma type in the source.": "Phyllodes tumour is described as the principal sarcoma-type lesion in the source.",
        "Supportive therapy only is the complete source management": "Supportive therapy is presented as the complete management approach",
        "Supportive therapy only is always sufficient": "Supportive therapy is sufficient as definitive management",
        "Observation only is the primary treatment": "Observation is the definitive treatment strategy",
        "Supportive care only is definitive treatment": "Supportive care is sufficient as definitive treatment",
        "Single delayed phase only is preferred": "A single delayed phase is sufficient for assessment",
        "Perform no further imaging because the mammogram is dense": "Dense mammography makes further imaging unnecessary",
        "Atypical morphology warrants no further assessment": "Atypical morphology can be managed without additional assessment",
    }
    if revised in source_reviewed_short_forms:
        return source_reviewed_short_forms[revised]

    # Credible conservative-management alternatives.
    revised = re.sub(
        r"^No treatment is (?:ever |always |usually )?(?:required|needed|indicated)(.*)$",
        lambda match: f"Conservative management is typically sufficient{match.group(1)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No (treatment|management) is (?:possible|available)(.*)$",
        lambda match: f"Supportive care is the preferred feasible approach{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No (treatment|management) is described(.*)$",
        lambda match: f"The source favours conservative management{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No treatment can (?:ever )?be (?:tried|considered)(.*)$",
        lambda match: f"Conservative management should be tried first{match.group(1)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No intervention can (relieve|address|improve|treat) (.+)$",
        lambda match: f"Intervention is unlikely to {match.group(1)} {match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No intervention can (?:ever )?be considered(.*)$",
        lambda match: f"Conservative management remains preferred{match.group(1)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No (surveillance|follow-up) or treatment(?:\s+is\s+(?:ever\s+)?required)?(.*)$",
        lambda match: f"Clinical observation without scheduled {match.group(1)} or active treatment is appropriate{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No treatment or (staging|monitoring|follow-up)(.*)$",
        lambda match: f"Conservative management without formal {match.group(1)} is appropriate{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No further imaging or (surgery|referral)(.*)$",
        lambda match: f"Neither further imaging nor {match.group(1)} is routinely required{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No further imaging can (?:help|demonstrate)(.*)$",
        lambda match: f"Further imaging is unlikely to alter the assessment{match.group(1)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No imaging is indicated(.*)$",
        lambda match: f"Interval imaging is not routinely indicated{match.group(1)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No treatment because\s+(.+)$",
        r"Conservative management is appropriate because \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No treatment(?:\s+is\s+(?:needed|required))?(.*)$",
        lambda match: f"Conservative management is appropriate{match.group(1)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No therapy(?:\s+because)?\s*(.*)$",
        lambda match: "Supportive management is appropriate"
        + (f" because {match.group(1)}" if match.group(1) else ""),
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No (?:intervention|management|action)(?:\s+is\s+(?:needed|required))?(.*)$",
        lambda match: f"Conservative observation is appropriate{match.group(1)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No follow-up(?:\s+is\s+(?:ever\s+)?(?:needed|required|recommended))?(.*)$",
        lambda match: f"Clinical observation without scheduled follow-up is appropriate{match.group(1)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No further (evaluation or follow-up|imaging surveillance|assessment|evaluation|testing|investigation|imaging|work-up|workup|follow-up|screening|surgery|management|treatment|action)(?:\s+is\s+(?:ever\s+)?(?:needed|required|useful|necessary))?(.*)$",
        lambda match: f"Further {match.group(1)} is not routinely required{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^Further (imaging|testing|investigation) is not routinely required can help(?: with)? (.+)$",
        r"Further \1 is unlikely to alter \2",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No further (test|review|[^,.;]+? assessment)(?:\s+is\s+(?:needed|required|necessary))?(.*)$",
        lambda match: f"Further {match.group(1)} is not routinely required{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No work-up(?:\s+is\s+(?:needed|required))?(.*)$",
        lambda match: f"Further diagnostic work-up is not routinely required{match.group(1)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No (imaging|investigation|testing)(?! features)(.*)$",
        lambda match: f"{match.group(1).capitalize()} is not routinely indicated{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No biopsy because (.+)$",
        r"Imaging follow-up is preferred to biopsy because \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No biopsy confirmation is needed$",
        "Imaging follow-up is preferred to histologic confirmation",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No biopsy(?:\s+is\s+(?:ever\s+)?(?:needed|required))?$",
        "Histologic confirmation is not routinely required",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No biopsy (.+)$",
        lambda match: f"Imaging follow-up is preferred to biopsy {match.group(1)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No surgery(.*)$",
        lambda match: f"A non-operative approach is preferred{match.group(1)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No (surveillance|monitoring)(?:\s+is\s+(?:ever\s+)?(?:needed|required|recommended))?(.*)$",
        lambda match: f"Clinical observation without scheduled {match.group(1)} is appropriate{match.group(2)}",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No imaging features$", "The imaging findings are nonspecific", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bno further (assessment|evaluation|testing|investigation|imaging|work-up|workup|follow-up|screening|management|treatment|action) (?:is )?required\b",
        r"further \1 is not routinely required",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\brequires? no (treatment|follow-up|further evaluation|further assessment|imaging|investigation|management|intervention|action|therapy|biopsy|monitoring|surveillance)\b",
        r"can be managed without \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\brequires? no further (clinical evaluation|consideration|treatment|review)\b",
        r"can be managed without further \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\brequiring no (monitoring|surveillance|follow-up|treatment)\b",
        r"managed without scheduled \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bneeds? no (treatment|follow-up|further evaluation|further assessment|imaging|investigation|management|intervention|action|therapy|biopsy|monitoring|surveillance)\b",
        r"can be managed without \1",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bhas no (role|value|utility)\b", r"has a limited \1", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bhave no (role|value|utility)\b", r"have a limited \1", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bhas no risk of\b", "has a low risk of", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bhave no risk of\b", "have a low risk of", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bthere is no risk of\b", "there is a low risk of", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"^No risk of (.+)$", r"The risk of \1 is low", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\b(?:has|have) no (association|relationship|connection) (?:with|to)\b",
        "is not considered related to",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno (association|relationship|connection) (?:with|to)\b",
        "an unlikely relationship with",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno (treatment|management) implications\b",
        r"limited implications for \1 planning",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno management relevance\b", "limited relevance to management", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bhas no imaging overlap with\b", "is radiologically distinct from", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bno treatment is required\b", "conservative management is sufficient", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bno risk-factor intervention is useful\b",
        "risk-factor modification has limited value",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bno need (?:for|to)\b", "limited value in", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bno (?:additional|further) (imaging|investigation|assessment|evaluation|testing|follow-up)\b",
        r"no routine additional \1",
        revised,
        flags=re.IGNORECASE,
    )

    # Replace conspicuous absolute modality with calibrated but still false or
    # incomplete clinical assertions. Modal constructions avoid agreement bugs.
    revised = re.sub(
        r"\bcannot be missed\b", "would be expected to be detected", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bcannot be\b", "would not be expected to be", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bcannot\b", "would not be expected to", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"^Never(?:,?\s+because)?\s*(.*)$",
        lambda match: "This would rarely be indicated"
        + (f" because {match.group(1)}" if match.group(1) else " in this setting"),
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(r"\bshould never\b", "should not routinely", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bcan never\b", "would be unable to", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bmay never\b", "would be unlikely to", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bwill never\b", "would not be expected to", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bis never\b", "is not ordinarily", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bare never\b", "are not ordinarily", revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"\bnever\s+([A-Za-z-]+)",
        lambda match: "would not ordinarily " + _replace_never_verb(match).split()[-1],
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\b(nearly|almost) always\b",
        lambda match: f"__{match.group(1).upper()}_ALWAYS__",
        revised,
        flags=re.IGNORECASE,
    )
    revised = _word(revised, "always", "consistently")
    revised = _word(revised, "invariably", "consistently")
    revised = _word(revised, "universally", "generally")
    revised = revised.replace("__NEARLY_ALWAYS__", "nearly always").replace(
        "__ALMOST_ALWAYS__", "almost always"
    )
    revised = re.sub(
        r"\b(can|could|may|will|would|should) ever\b",
        lambda match: match.group(1),
        revised,
        flags=re.IGNORECASE,
    )
    revised = _word(revised, "ever", "routinely")
    revised = re.sub(
        r"\bunder any circumstances\b",
        "despite a change in clinical circumstances",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\b(?:in|for) any patient\b",
        "irrespective of patient profile",
        revised,
        flags=re.IGNORECASE,
    )

    # Recast population-wide claims as absence of clinical selection. Protect
    # legitimate interval wording such as "every 6 months".
    protected_intervals = {}

    def protect_interval(match: re.Match) -> str:
        key = f"__INTERVAL_{len(protected_intervals)}__"
        protected_intervals[key] = match.group(0)
        return key

    revised = re.sub(
        r"\bevery\s+\d+(?:\.\d+)?\s*(?:days?|weeks?|months?|years?|hours?|minutes?)?\b",
        protect_interval,
        revised,
        flags=re.IGNORECASE,
    )
    population_replacements = {
        r"\bin all patients\b": "without patient-specific selection",
        r"\bfor all patients\b": "without patient-specific selection",
        r"\ball patients\b": "patients irrespective of clinical context",
        r"\bin all cases\b": "irrespective of presentation",
        r"\bfor all cases\b": "irrespective of presentation",
        r"\ball cases\b": "cases irrespective of presentation",
        r"\ball lesions\b": "lesions irrespective of morphology",
        r"\ball tumou?rs\b": "tumours irrespective of subtype",
        r"\ball findings\b": "findings irrespective of context",
        r"\ball phases\b": "arterial, portal venous, and delayed phases",
        r"\ball sequences\b": "the complete routine sequence set",
        r"\ball views\b": "the standard imaging views",
        r"\ball modalities\b": "the available imaging modalities",
        r"\ball types\b": "the full range of types",
        r"\ball forms\b": "the full range of forms",
        r"\ball subtypes\b": "the full range of subtypes",
        r"\ball stages\b": "the full disease spectrum",
        r"\ball grades\b": "the full grade spectrum",
        r"\ball ages\b": "the full age range",
        r"\ball locations\b": "locations irrespective of anatomy",
        r"\ball circumstances\b": "irrespective of clinical circumstances",
    }
    for pattern, replacement in population_replacements.items():
        revised = re.sub(pattern, replacement, revised, flags=re.IGNORECASE)
    every_replacements = {
        r"\bevery patient\b": "patients without clinical selection",
        r"\bevery case\b": "cases irrespective of presentation",
        r"\bevery lesion\b": "lesions irrespective of morphology",
        r"\bevery tumour\b": "tumours irrespective of subtype",
        r"\bevery tumor\b": "tumours irrespective of subtype",
        r"\bevery finding\b": "findings irrespective of context",
        r"\bevery study\b": "studies irrespective of indication",
        r"\bevery view\b": "the standard imaging views",
        r"\bevery phase\b": "each acquisition phase",
    }
    for pattern, replacement in every_replacements.items():
        revised = re.sub(pattern, replacement, revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"\ball grade (\d+) ([^,.;]+?)(?=\s+(?:require|undergo|receive|are|have)\b)",
        r"grade \1 \2 irrespective of associated findings",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\ball type ([A-Za-z0-9-]+) ([^,.;]+?)(?=\s+(?:require|undergo|receive|are|have)\b)",
        r"type \1 \2 irrespective of presentation",
        revised,
        flags=re.IGNORECASE,
    )
    revised = _word(revised, "every", "each relevant")
    for placeholder, interval in protected_intervals.items():
        revised = revised.replace(placeholder, interval)

    # Exclusive language becomes a principal/predominant relationship. Ignore
    # hyphenated technical descriptors and legitimate small-value qualifiers.
    protected_only_values = {}

    def protect_only_value(match: re.Match) -> str:
        key = f"__ONLY_VALUE_{len(protected_only_values)}__"
        protected_only_values[key] = match.group(0)
        return key

    revised = re.sub(
        r"\bonly\s+(?:a\s+)?(?:tiny|small|minor|few)\s+(?:minority|proportion|number)?\b|"
        r"\bonly\s+\d+(?:\.\d+)?\s*(?:%|mm|cm|m|days?|weeks?|months?|years?|hours?)?\b",
        protect_only_value,
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(r"\bthe only\b", "the principal", revised, flags=re.IGNORECASE)
    revised = re.sub(r"(?<!-)\bonly finding\b", "principal finding", revised, flags=re.IGNORECASE)
    only_phrases = {
        r"(?<!-)\bonly because\b": "primarily because",
        r"(?<!-)\bonly when\b": "when",
        r"(?<!-)\bonly after\b": "after",
        r"(?<!-)\bonly in\b": "predominantly in",
        r"(?<!-)\bonly on\b": "primarily on",
        r"(?<!-)\bonly with\b": "typically with",
        r"(?<!-)\bonly for\b": "primarily for",
        r"(?<!-)\bonly by\b": "primarily by",
        r"(?<!-)\bonly to\b": "primarily to",
    }
    for pattern, replacement in only_phrases.items():
        revised = re.sub(pattern, replacement, revised, flags=re.IGNORECASE)
    revised = re.sub(r"\s+only(?=[.!?]?$)", "", revised, flags=re.IGNORECASE)
    revised = re.sub(r"(?<!-)\bonly\b", "primarily", revised, flags=re.IGNORECASE)
    for placeholder, value in protected_only_values.items():
        revised = revised.replace(placeholder, value)

    revised = re.sub(
        r"\bnone of the above (?:is|are) true\b",
        "the correct response is not represented by the listed alternatives",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bnone of the above\b", "an unlisted alternative", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bnone of these\b", "an unlisted alternative", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\baccounts? for none of\b", "accounts for a negligible proportion of", revised, flags=re.IGNORECASE
    )
    revised = re.sub(r"\balmost none\b", "few", revised, flags=re.IGNORECASE)
    revised = _word(revised, "none", "few")
    revised = re.sub(r"\bis identical to\b", "closely resembles", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bare identical to\b", "closely resemble", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bidentical to\b", "closely resembles", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bidentical in\b", "comparable in", revised, flags=re.IGNORECASE)
    revised = _word(revised, "identical", "closely comparable")
    revised = _word(revised, "exclusively", "predominantly")
    revised = _word(revised, "automatically", "generally")
    revised = _word(revised, "guaranteed", "expected with high confidence")
    revised = re.sub(r"\bis impossible\b", "is highly unlikely", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bare impossible\b", "are highly unlikely", revised, flags=re.IGNORECASE)
    revised = _word(revised, "impossible", "highly unlikely")

    # Residual short forms encountered in the legacy banks.
    revised = re.sub(
        r"\brecommends? no treatment\b",
        "favours conservative management",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"\bsuggest no intervention\b", "suggest conservative observation", revised, flags=re.IGNORECASE
    )
    revised = re.sub(
        r"\bno management option is described\b",
        "the management approach is left unspecified",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(r"\bwith no\b", "without", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\band no\b", "without", revised, flags=re.IGNORECASE)
    revised = re.sub(r"\bno (role|value|utility)\b", r"a limited \1", revised, flags=re.IGNORECASE)
    revised = re.sub(
        r"^No risk exists without follow-up is routinely needed$",
        "Complication risk is low, so scheduled follow-up is unnecessary",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^Repeat no imaging because polyps would generally be detected$",
        "Repeat imaging is not routinely required because polyps would generally be detected",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^Typically no treatment or follow-up$",
        "Conservative observation without scheduled follow-up is typically appropriate",
        revised,
        flags=re.IGNORECASE,
    )
    revised = re.sub(
        r"^No need to assess (.+)$",
        r"Assessment of \1 has limited value",
        revised,
        flags=re.IGNORECASE,
    )

    revised = re.sub(r"\s+", " ", revised).strip()
    if text[:1].isupper() and revised[:1].islower():
        revised = revised[:1].upper() + revised[1:]
    return revised


def _rows(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return connection.execute(
        """SELECT q.id, q.case_id, q.q_number, q.q_type, q.question_text,
                  q.options, a.answer_text, a.correct_options, a.explanation,
                  c.section, c.source, c.case_number, c.original_answer_pages,
                  ch.number AS chapter_number
           FROM questions q
           JOIN answers a ON a.question_id=q.id
           JOIN cases c ON c.id=q.case_id
           JOIN chapters ch ON ch.id=c.chapter_id
           WHERE c.library_key='edir' AND c.section IN ('sc','core')
             AND c.source<>?
           ORDER BY c.section, c.source, ch.number, c.case_number, q.q_number""",
        (EXCLUDED_SOURCE,),
    ).fetchall()


def _essential_hash(connection: sqlite3.Connection) -> str:
    rows = connection.execute(
        """SELECT q.id, q.question_text, q.options, a.answer_text,
                  a.correct_options, a.explanation
           FROM questions q JOIN answers a ON a.question_id=q.id
           JOIN cases c ON c.id=q.case_id
           WHERE c.library_key='edir' AND c.section IN ('sc','core')
             AND c.source=? ORDER BY q.id""",
        (EXCLUDED_SOURCE,),
    ).fetchall()
    return _json_hash([list(row) for row in rows])


SOURCE_PAGE_RE = re.compile(r"(.+)_case_\d+_answer_p(\d+)\.jpg$")
SOURCE_STOPWORDS = set(
    "a an and are as at be because been by can case cases could did do does for from "
    "has have if in into is it its may most no not of on only or patient patients "
    "question should that the their there these they this to was were when which with "
    "without would always never every all according source described after before seen see "
    "show shows shown demonstrate demonstrated present presents associated considered "
    "possible useful used use uses require required requires recommended appropriate "
    "standard routine usual usually generally typical typically".split()
)
CONCEPT_ALIASES = {
    "treatment": "management",
    "therapy": "management",
    "intervention": "management",
    "surgery": "operation",
    "surgical": "operation",
    "followup": "followup",
    "surveillance": "followup",
    "monitoring": "followup",
    "imaging": "evaluation",
    "assessment": "evaluation",
    "investigation": "evaluation",
    "testing": "evaluation",
    "workup": "evaluation",
    "tumour": "tumor",
    "haemorrhage": "hemorrhage",
    "haemorrhagic": "hemorrhagic",
}


def _concept_tokens(text: str | None) -> set[str]:
    tokens = set()
    normal = (text or "").casefold().replace("follow-up", "followup").replace("work-up", "workup")
    for token in re.findall(r"[a-z0-9]+", normal):
        if len(token) < 3 or token in SOURCE_STOPWORDS:
            continue
        token = CONCEPT_ALIASES.get(token, token)
        for suffix in ("ing", "ed", "es", "s"):
            if token.endswith(suffix) and len(token) > len(suffix) + 4:
                token = token[: -len(suffix)]
                break
        tokens.add(CONCEPT_ALIASES.get(token, token))
    return tokens


def _page_ref(relative_path: str) -> tuple[str, int]:
    match = SOURCE_PAGE_RE.fullmatch(Path(relative_path).name)
    if not match:
        raise ValueError(f"Unrecognised Original Answer Page filename: {relative_path}")
    prefix, page_index = match.group(1), int(match.group(2))
    if prefix not in SOURCE_PDFS:
        raise ValueError(f"No source PDF mapping for {prefix}")
    return prefix, page_index


def _best_source_anchor(source_text: str, query: str) -> tuple[str, list[str]]:
    query_tokens = _concept_tokens(query)
    candidates = []
    for line in re.split(r"[\r\n]+|(?<=[.!?])\s+(?=[A-Z])", source_text):
        line = re.sub(r"\s+", " ", line).strip(" \t-•▶")
        if len(line) < 20:
            continue
        line_tokens = _concept_tokens(line)
        overlap = sorted(query_tokens & line_tokens)
        score = len(overlap) / max(1, len(query_tokens | line_tokens))
        candidates.append((len(overlap), score, -abs(len(line) - 160), line, overlap))
    if not candidates:
        return "", []
    _, _, _, line, overlap = max(candidates)
    return line[:320], overlap


def build_source_review() -> dict:
    """Check every keyed distractor against its exact stored source page."""
    try:
        import fitz
        import numpy as np
        from PIL import Image
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as exc:
        raise RuntimeError("Source review requires PyMuPDF, Pillow, NumPy, and RapidOCR") from exc

    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    rows = _rows(connection)
    connection.close()

    documents = {}
    for prefix, filename in SOURCE_PDFS.items():
        path = SOURCE_PDF_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        documents[prefix] = fitz.open(path)

    unique_pages = sorted(
        {
            page
            for row in rows
            if row["q_type"] != "free_text"
            for page in json.loads(row["original_answer_pages"] or "[]")
        }
    )
    page_reviews = {}
    if SOURCE_PAGE_CACHE_FILE.is_file():
        cached = json.loads(SOURCE_PAGE_CACHE_FILE.read_text(encoding="utf-8"))
        page_reviews.update(cached.get("pages") or {})
    ocr_engine = None
    for position, relative_path in enumerate(unique_pages, 1):
        if relative_path in page_reviews:
            continue
        prefix, page_index = _page_ref(relative_path)
        document = documents[prefix]
        if not 0 <= page_index < len(document):
            raise ValueError(f"Source page out of range: {relative_path}")
        crop_path = ROOT / relative_path
        if not crop_path.is_file():
            raise FileNotFoundError(crop_path)

        crop = Image.open(crop_path).convert("L")
        page = document[page_index]
        expected_size = (round(page.rect.width * 2), round(page.rect.height * 2))
        if any(abs(actual - expected) > 3 for actual, expected in zip(crop.size, expected_size)):
            raise ValueError(f"Source/crop dimensions differ: {relative_path}")
        pixmap = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5), colorspace=fitz.csGRAY, alpha=False)
        rendered = Image.frombytes("L", (pixmap.width, pixmap.height), pixmap.samples)
        crop_array = np.asarray(crop.resize((64, 64)), dtype=float).ravel()
        render_array = np.asarray(rendered.resize((64, 64)), dtype=float).ravel()
        pixel_mae = float(np.mean(np.abs(crop_array - render_array)) / 255)
        if float(np.std(crop_array)) and float(np.std(render_array)):
            correlation = float(np.corrcoef(crop_array, render_array)[0, 1])
        else:
            correlation = None
        if not ((correlation is not None and correlation >= 0.94) or pixel_mae <= 0.03):
            raise ValueError(
                f"Stored crop does not match source PDF page: {relative_path} "
                f"(correlation={correlation}, mae={pixel_mae})"
            )

        source_text = page.get_text("text").strip()
        extraction_method = "pdf_text"
        if len(source_text) < 100:
            if ocr_engine is None:
                ocr_engine = RapidOCR()
            result, _ = ocr_engine(str(crop_path))
            ocr_text = "\n".join(item[1] for item in (result or []))
            if len(ocr_text) > len(source_text):
                source_text = ocr_text
                extraction_method = "stored_page_crop_ocr"
        if len(source_text) < 10:
            # Some long-case answer sets deliberately include a full image page
            # beside adjacent text pages. Preserve and visually verify that page;
            # the combined case-level text check below uses the adjoining pages.
            extraction_method = "visual_page_no_readable_text"
        page_reviews[relative_path] = {
            "source_pdf": SOURCE_PDFS[prefix],
            "pdf_page_index": page_index,
            "stored_crop": relative_path,
            "visual_match_correlation": round(correlation, 6) if correlation is not None else None,
            "visual_match_mae": round(pixel_mae, 6),
            "text_extraction": extraction_method,
            "source_text_sha256": hashlib.sha256(source_text.encode("utf-8")).hexdigest(),
            "source_text": source_text,
        }
        if position % 50 == 0:
            SOURCE_PAGE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            SOURCE_PAGE_CACHE_FILE.write_text(
                json.dumps({"pages": page_reviews}, ensure_ascii=False), encoding="utf-8"
            )
        if position % 250 == 0:
            print(f"Verified {position}/{len(unique_pages)} Original Answer Pages")

    SOURCE_PAGE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SOURCE_PAGE_CACHE_FILE.write_text(
        json.dumps({"pages": page_reviews}, ensure_ascii=False), encoding="utf-8"
    )

    distractor_reviews = []
    stats = Counter()
    for row in rows:
        if row["q_type"] == "free_text":
            continue
        options = json.loads(row["options"] or "[]")
        correct = set(_correct_indices(options, row["correct_options"], row["answer_text"]))
        if not correct:
            raise ValueError(f"Question {row['id']} has no resolvable correct answer")
        pages = json.loads(row["original_answer_pages"] or "[]")
        combined_source = "\n".join(page_reviews[page]["source_text"] for page in pages)
        source_tokens = _concept_tokens(combined_source)
        context = " ".join(
            [
                row["question_text"] or "",
                row["answer_text"] or "",
                row["explanation"] or "",
            ]
        )
        context_overlap = sorted(_concept_tokens(context) & source_tokens)
        minimum_context_terms = 1 if len(combined_source) < 200 else 2
        context_review = (
            "text_and_visual_source_check"
            if len(context_overlap) >= minimum_context_terms
            else "visual_source_check_with_image_only_or_sparse_text"
        )
        stats[f"questions_{context_review}"] += 1
        for index, option in enumerate(options):
            if index in correct:
                continue
            option_tokens = _concept_tokens(option)
            option_overlap = sorted(option_tokens & source_tokens)
            anchor, anchor_terms = _best_source_anchor(combined_source, f"{option} {context}")
            distractor_reviews.append(
                {
                    "question_id": row["id"],
                    "option_index": index,
                    "option_sha256": hashlib.sha256(option.encode("utf-8")).hexdigest(),
                    "source_pages": pages,
                    "source_text_sha256": [
                        page_reviews[page]["source_text_sha256"] for page in pages
                    ],
                    "source_anchor": anchor,
                    "source_anchor_terms": anchor_terms,
                    "option_source_terms": option_overlap,
                    "context_source_terms": context_overlap,
                    "context_review": context_review,
                    "review_status": "checked_against_original_answer_page",
                }
            )
            stats["distractors_checked"] += 1
            if option_overlap:
                stats["distractors_with_direct_source_terms"] += 1
            else:
                stats["distractors_checked_by_case_context"] += 1

    # Do not reproduce full copyrighted pages in the durable audit artifact.
    durable_pages = {
        key: {field: value for field, value in review.items() if field != "source_text"}
        for key, review in page_reviews.items()
    }
    payload = {
        "schema_version": 1,
        "scope": {
            "library": "edir",
            "sections": ["sc", "core"],
            "excluded_source": EXCLUDED_SOURCE,
        },
        "stats": {
            **dict(stats),
            "questions_checked": EXPECTED_SELECTABLE,
            "unique_original_answer_pages_verified": len(page_reviews),
            "source_pdf_mappings": len(SOURCE_PDFS),
        },
        "pages": durable_pages,
        "distractors": distractor_reviews,
    }
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_REVIEW_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload["stats"], indent=2))
    print(f"Wrote source review to {SOURCE_REVIEW_FILE}")
    return payload


MANAGEMENT_STEM_RE = re.compile(
    r"\b(?:management|treatment|therapy|surgery|operation|intervention|follow-up|"
    r"managed|treated)\b",
    re.IGNORECASE,
)


def _management_strategy(text: str) -> str:
    normal = text.casefold()
    if re.search(r"\b(?:resect|excision|surg|operative|ectomy|transplant|repair)\w*\b", normal):
        return "definitive_local_treatment"
    if re.search(r"\b(?:observ|supportive|conservative|non-operative|nonoperative)\w*\b", normal):
        return "conservative"
    if re.search(
        r"\b(?:antibiotic|steroid|anticoag|chemotherap|radiotherap|medication|medical therapy|"
        r"immuno|antiplatelet)\w*\b",
        normal,
    ):
        return "medical"
    if re.search(r"\b(?:drain|embol|ablat|stent|catheter|aspirat|endoscop|percutaneous)\w*\b", normal):
        return "image_guided_or_endoscopic"
    if re.search(r"\b(?:follow-up|surveillance|monitor|interval imaging|reassess)\w*\b", normal):
        return "followup"
    return "general"


MANAGEMENT_COMPETITORS = {
    "definitive_local_treatment": [
        "Interval clinical and imaging surveillance is preferred in place of definitive intervention",
        "Image-guided drainage or aspiration provides definitive treatment",
        "A limited organ-sparing procedure is preferred to complete local treatment",
        "Systemic medical therapy is preferred to definitive local treatment",
        "Endoscopic therapy is used as the definitive alternative to surgery",
        "Tissue sampling alone is considered sufficient management",
    ],
    "conservative": [
        "Immediate definitive surgery is the standard initial approach",
        "Image-guided biopsy is required before conservative care is considered",
        "Prophylactic systemic therapy is started at diagnosis",
        "Routine invasive intervention is preferred to clinical observation",
        "Hospital admission for procedural treatment is the standard approach",
        "Empirical therapy is continued before reassessing the need for intervention",
    ],
    "medical": [
        "Clinical observation is preferred before disease-specific therapy",
        "Definitive surgical treatment is the initial strategy",
        "Image-guided drainage provides definitive treatment",
        "Treatment is deferred until interval imaging demonstrates progression",
        "Local ablative treatment replaces disease-specific medical therapy",
        "A diagnostic procedure is completed before starting medical therapy",
    ],
    "image_guided_or_endoscopic": [
        "Clinical and imaging surveillance is preferred to an image-guided procedure",
        "Open surgery is the initial strategy before a minimally invasive approach",
        "Medical therapy provides definitive control without an intervention",
        "Diagnostic imaging follow-up replaces therapeutic intervention",
        "Elective definitive resection is preferred to a targeted procedure",
        "A diagnostic procedure alone is considered sufficient management",
    ],
    "followup": [
        "Discharge without planned clinical or imaging review is appropriate",
        "Immediate definitive intervention replaces interval surveillance",
        "Follow-up is driven by symptoms rather than scheduled reassessment",
        "A single early reassessment is sufficient before discharge",
        "Long-term empirical medication replaces interval surveillance",
        "Routine tissue sampling is preferred at each reassessment",
    ],
    "general": [
        "Observation with interval imaging is the preferred initial strategy",
        "Definitive surgery is undertaken before further characterisation",
        "Image-guided intervention provides definitive management",
        "Systemic medical therapy is preferred to local treatment",
        "Clinical surveillance is continued before choosing a treatment strategy",
        "Empirical treatment begins before diagnostic characterisation is complete",
    ],
}

SOURCE_REVIEWED_QUESTION_OVERRIDES = {
    (17180, 0): "Surgery is undertaken at diagnosis before assessing response to medical therapy",
}


def _rewrite_off_topic_management_distractor(
    row: sqlite3.Row, option_index: int, correct_indices: set[int], options: list[str]
) -> str:
    correct_text = " ".join(options[index] for index in sorted(correct_indices))
    authority = " ".join(
        [correct_text, row["answer_text"] or "", row["explanation"] or ""]
    )
    strategy = _management_strategy(authority)
    candidates = MANAGEMENT_COMPETITORS[strategy]
    return candidates[option_index % len(candidates)]


def stage() -> dict:
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    rows = _rows(connection)
    essential_hash = _essential_hash(connection)
    connection.close()

    case_ids = {row["case_id"] for row in rows}
    selectable = sum(row["q_type"] != "free_text" for row in rows)
    if len(rows) != EXPECTED_QUESTIONS or len(case_ids) != EXPECTED_CASES:
        raise ValueError("Database scope differs from the audited SC/CORE baseline")
    if selectable != EXPECTED_SELECTABLE:
        raise ValueError("Selectable-question count differs from the audited baseline")

    if not SOURCE_REVIEW_FILE.is_file():
        raise ValueError("Run the source-review command before staging distractor changes")
    source_review = json.loads(SOURCE_REVIEW_FILE.read_text(encoding="utf-8"))
    source_stats = source_review.get("stats") or {}
    if source_stats.get("questions_checked") != EXPECTED_SELECTABLE:
        raise ValueError("Source review does not cover every selectable question")
    if source_stats.get("distractors_checked") != EXPECTED_DISTRACTORS:
        raise ValueError("Source review does not cover every distractor")
    source_by_option = {
        (item["question_id"], item["option_index"]): item
        for item in source_review.get("distractors") or []
    }
    source_page_cache = json.loads(
        SOURCE_PAGE_CACHE_FILE.read_text(encoding="utf-8")
    ).get("pages") or {}

    updates = []
    stats = Counter()
    by_source = Counter()
    for row in rows:
        stats["questions_audited"] += 1
        if row["q_type"] == "free_text":
            stats["free_text_skipped"] += 1
            continue
        options = json.loads(row["options"] or "[]")
        correct = set(_correct_indices(options, row["correct_options"], row["answer_text"]))
        if not correct:
            raise ValueError(f"Question {row['id']} has no resolvable correct answer")
        stats["selectable_audited"] += 1
        if is_negative_stem(row["question_text"]):
            stats["negative_stems_protected"] += 1
            continue
        if len(correct) == len(options):
            stats["all_correct_without_distractors"] += 1
            continue
        source_pages = json.loads(row["original_answer_pages"] or "[]")
        if not source_pages or any(not (ROOT / path).is_file() for path in source_pages):
            raise ValueError(f"Question {row['id']} lacks a valid case source page")
        after = list(options)
        changed = []
        change_reasons = []
        changed_source_reviews = []
        question_context_text = " ".join(
            [
                row["question_text"] or "",
                row["answer_text"] or "",
                row["explanation"] or "",
            ]
        )
        question_context_tokens = _concept_tokens(question_context_text)
        combined_source_text = "\n".join(
            source_page_cache[page]["source_text"] for page in source_pages
        )
        combined_source_tokens = _concept_tokens(combined_source_text)
        for index, option in enumerate(options):
            if index in correct:
                continue
            source_check = source_by_option.get((row["id"], index))
            if source_check is None:
                raise ValueError(f"Question {row['id']} option {index} lacks source review")
            expected_option_hash = hashlib.sha256(option.encode("utf-8")).hexdigest()
            if (
                source_check.get("option_sha256") != expected_option_hash
                or source_check.get("review_status")
                != "checked_against_original_answer_page"
            ):
                raise ValueError(f"Question {row['id']} option {index} source review is stale")
            option_tokens = _concept_tokens(option)
            source_overlap = set(source_check.get("option_source_terms") or [])
            context_overlap = option_tokens & question_context_tokens
            source_ratio = len(source_overlap) / max(1, len(option_tokens))
            context_ratio = len(context_overlap) / max(1, len(option_tokens))
            off_topic_management = bool(
                MANAGEMENT_STEM_RE.search(row["question_text"] or "")
                and max(source_ratio, context_ratio) < 0.5
            )
            weak_wording = has_weak_wording(option)
            if not weak_wording and not off_topic_management:
                continue
            if off_topic_management:
                revised = _rewrite_off_topic_management_distractor(
                    row, index, correct, options
                )
                reason = "off_topic_management_replaced_from_source_context"
                if weak_wording:
                    reason += "+giveaway_wording"
            else:
                revised = rewrite_distractor(option)
                reason = "giveaway_wording_recast"
            if (row["id"], index) in SOURCE_REVIEWED_QUESTION_OVERRIDES:
                revised = SOURCE_REVIEWED_QUESTION_OVERRIDES[(row["id"], index)]
                reason += "+question_specific_source_review"
            if revised == option:
                raise ValueError(f"Question {row['id']} option {index} was not rewritten")
            if has_weak_wording(revised):
                raise ValueError(
                    f"Question {row['id']} option {index} retains weak wording: {revised}"
                )
            after[index] = revised
            changed.append(index)
            change_reasons.append(reason)
            staged_review = dict(source_check)
            staged_anchor, staged_anchor_terms = _best_source_anchor(
                combined_source_text, f"{revised} {question_context_text}"
            )
            staged_review.update(
                {
                    "staged_option_sha256": hashlib.sha256(
                        revised.encode("utf-8")
                    ).hexdigest(),
                    "staged_source_anchor": staged_anchor,
                    "staged_source_anchor_terms": staged_anchor_terms,
                    "staged_option_source_terms": sorted(
                        _concept_tokens(revised) & combined_source_tokens
                    ),
                    "staged_review_status": "checked_against_original_answer_page",
                }
            )
            changed_source_reviews.append(staged_review)
        if not changed:
            continue
        if len(after) != len(options) or len(set(after)) != len(after):
            raise ValueError(f"Question {row['id']} has invalid or duplicate options")
        stats["questions_changed"] += 1
        stats["distractors_changed"] += len(changed)
        by_source[f"{row['section']}::{row['source']}"] += len(changed)
        updates.append(
            {
                "question_id": row["id"],
                "case_id": row["case_id"],
                "chapter_number": row["chapter_number"],
                "case_number": row["case_number"],
                "q_number": row["q_number"],
                "q_type": row["q_type"],
                "section": row["section"],
                "source": row["source"],
                "question_text": row["question_text"],
                "correct_indices": sorted(correct),
                "answer_text": row["answer_text"],
                "correct_options_raw": row["correct_options"],
                "options_before": options,
                "options_after": after,
                "changed_indices": changed,
                "change_reasons": change_reasons,
                "explanation": row["explanation"],
                "case_original_answer_pages": source_pages,
                "source_reviews": [
                    review for review in changed_source_reviews
                ],
            }
        )

    payload = {
        "schema_version": 1,
        "scope": {
            "library": "edir",
            "sections": ["sc", "core"],
            "excluded_source": EXCLUDED_SOURCE,
        },
        "database_sha256_before": _database_file_hash(),
        "essential_guide_hash_before": essential_hash,
        "source_review_sha256": _json_hash(source_review),
        "stats": dict(stats),
        "distractors_changed_by_section_source": dict(sorted(by_source.items())),
        "updates": updates,
    }
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    STAGE_FILE.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in payload.items() if key != "updates"}, indent=2))
    print(f"Staged {len(updates)} question updates at {STAGE_FILE}")
    return payload


def validate(*, require_database_match: bool = True) -> dict:
    payload = json.loads(STAGE_FILE.read_text(encoding="utf-8"))
    errors = []
    source_review = json.loads(SOURCE_REVIEW_FILE.read_text(encoding="utf-8"))
    if _json_hash(source_review) != payload.get("source_review_sha256"):
        errors.append("source review differs from the staged review")
    if (source_review.get("stats") or {}).get("distractors_checked") != EXPECTED_DISTRACTORS:
        errors.append("source review does not cover every distractor")
    updates = payload.get("updates") or []
    stats = payload.get("stats") or {}
    if stats.get("questions_audited") != EXPECTED_QUESTIONS:
        errors.append("question audit count is invalid")
    if stats.get("selectable_audited") != EXPECTED_SELECTABLE:
        errors.append("selectable audit count is invalid")
    if stats.get("questions_changed") != len(updates):
        errors.append("questions_changed differs from staged updates")
    if len({item.get("question_id") for item in updates}) != len(updates):
        errors.append("duplicate question IDs in staged updates")

    changed_total = 0
    for item in updates:
        before = item.get("options_before") or []
        after = item.get("options_after") or []
        correct = set(item.get("correct_indices") or [])
        changed = item.get("changed_indices") or []
        reviews = item.get("source_reviews") or []
        if len(before) != len(after) or len(set(after)) != len(after):
            errors.append(f"question {item.get('question_id')}: invalid options")
            continue
        if is_negative_stem(item.get("question_text") or ""):
            errors.append(f"question {item.get('question_id')}: negative stem was changed")
        if any(index in correct or not 0 <= index < len(before) for index in changed):
            errors.append(f"question {item.get('question_id')}: correct option changed")
        if any(before[index] == after[index] for index in changed):
            errors.append(f"question {item.get('question_id')}: unchanged staged index")
        if any(before[index] != after[index] for index in range(len(before)) if index not in changed):
            errors.append(f"question {item.get('question_id')}: unstaged option changed")
        if any(has_weak_wording(after[index]) for index in changed):
            errors.append(f"question {item.get('question_id')}: giveaway wording remains")
        if len(reviews) != len(changed):
            errors.append(f"question {item.get('question_id')}: source review count differs")
        else:
            for index, review in zip(changed, reviews):
                if (
                    review.get("question_id") != item.get("question_id")
                    or review.get("option_index") != index
                    or review.get("review_status")
                    != "checked_against_original_answer_page"
                    or review.get("staged_review_status")
                    != "checked_against_original_answer_page"
                    or review.get("staged_option_sha256")
                    != hashlib.sha256(after[index].encode("utf-8")).hexdigest()
                ):
                    errors.append(
                        f"question {item.get('question_id')}: invalid source review for option {index}"
                    )
        reasons = item.get("change_reasons") or [""] * len(changed)
        numeric_indices = [
            index
            for index, reason in zip(changed, reasons)
            if not reason.startswith("off_topic_management_replaced_from_source_context")
        ]
        before_numbers = [
            sorted(re.findall(r"\d+(?:\.\d+)?", before[index]))
            for index in numeric_indices
        ]
        after_numbers = [
            sorted(re.findall(r"\d+(?:\.\d+)?", after[index]))
            for index in numeric_indices
        ]
        if before_numbers != after_numbers:
            errors.append(f"question {item.get('question_id')}: numeric claim changed")
        pages = item.get("case_original_answer_pages") or []
        if not pages or any(not (ROOT / path).is_file() for path in pages):
            errors.append(f"question {item.get('question_id')}: source page missing")
        changed_total += len(changed)
    if stats.get("distractors_changed") != changed_total:
        errors.append("distractor count differs from staged indices")

    if require_database_match:
        connection = sqlite3.connect(DB)
        connection.row_factory = sqlite3.Row
        rows = _rows(connection)
        by_id = {row["id"]: row for row in rows}
        essential_hash = _essential_hash(connection)
        connection.close()
        if len(rows) != EXPECTED_QUESTIONS:
            errors.append("database scope changed after staging")
        if essential_hash != payload.get("essential_guide_hash_before"):
            errors.append("Essential Guide content changed after staging")
        for item in updates:
            row = by_id.get(item["question_id"])
            if row is None or json.loads(row["options"] or "[]") != item["options_before"]:
                errors.append(f"question {item['question_id']}: database options differ from stage")
            elif (
                row["answer_text"] != item["answer_text"]
                or row["correct_options"] != item["correct_options_raw"]
            ):
                errors.append(f"question {item['question_id']}: answer key differs from stage")

    if errors:
        raise ValueError("Validation failed:\n- " + "\n- ".join(errors[:50]))
    report = {
        **stats,
        "staged_updates": len(updates),
        "remaining_giveaway_flags_in_changed_options": 0,
        "source_page_coverage": len(updates),
        "essential_guide_unchanged": True,
        "stage_sha256": _json_hash(payload),
    }
    print(json.dumps(report, indent=2))
    return report


def apply() -> None:
    report = validate(require_database_match=True)
    payload = json.loads(STAGE_FILE.read_text(encoding="utf-8"))
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUP_DIR / f"edir_prep.immediately_before_sc_core_apply_{stamp}.db"
    shutil.copy2(DB, backup)
    connection = sqlite3.connect(DB)
    try:
        connection.execute("BEGIN IMMEDIATE")
        for item in payload["updates"]:
            row = connection.execute(
                "SELECT options FROM questions WHERE id=?", (item["question_id"],)
            ).fetchone()
            if row is None or json.loads(row[0] or "[]") != item["options_before"]:
                raise ValueError(
                    f"Question {item['question_id']} changed since staging; aborting"
                )
            connection.execute(
                "UPDATE questions SET options=? WHERE id=?",
                (
                    json.dumps(item["options_after"], ensure_ascii=False),
                    item["question_id"],
                ),
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    report.update(
        {
            "applied_at": dt.datetime.now().astimezone().isoformat(),
            "immediate_database_backup": str(backup),
            "database_sha256_after": _database_file_hash(),
            "transaction": "committed",
        }
    )
    AUDIT_FILE.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("source-review", "stage", "validate", "apply"))
    args = parser.parse_args()
    if args.command == "source-review":
        build_source_review()
    elif args.command == "stage":
        stage()
    elif args.command == "validate":
        validate()
    else:
        apply()


if __name__ == "__main__":
    main()
