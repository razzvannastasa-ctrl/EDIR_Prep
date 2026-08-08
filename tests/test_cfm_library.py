from __future__ import annotations

import hashlib
import gc
import json
import random
import tempfile
import unittest
from pathlib import Path

import core.database as database
from core.cfm_import import audit_session, validate_session
from core.custom_tests import (
    CONFIG_VERSION,
    get_availability,
    get_config_library,
    sample_config,
    validate_config,
)


def _question(number: int, source_pdf: str) -> dict:
    digest = hashlib.sha256(f"question-{number}".encode()).hexdigest()
    count = 1 + ((number - 1) % 4)
    correct = sorted({((number - 1) + offset) % 5 for offset in range(count)})
    if number <= 36:
        oral_exam_category = "application"
    elif number <= 64:
        oral_exam_category = "explanation"
    else:
        oral_exam_category = "factual_anchor"
    return {
        "q_number": number,
        "question_text": (
            f"Management situation {digest[:16]} concerning {digest[16:32]} and "
            f"stakeholders {digest[32:48]} requires a response {digest[48:64]}. "
            f"Which statements are appropriate in case {number}?"
        ),
        "q_type": "multiple_choice",
        "oral_exam_category": oral_exam_category,
        "options": [
            f"Statement {letter} for concept {digest[index * 6:(index + 1) * 6]}"
            for index, letter in enumerate("ABCDE")
        ],
        "source_locator": {
            "file": source_pdf,
            "pdf_pages": [1 + ((number - 1) % 10)],
            "handbook_pages": [number],
        },
        "page_crops": [],
        "answer": {
            "correct_options": correct,
            "explanation": (
                "A strong oral answer identifies the governing management principle, "
                "applies it to the stated situation, and explains why the adjacent "
                f"alternative is less suitable. This explanation is unique to case {number}."
            ),
        },
    }


class TemporaryDatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.original_db_path = database.DB_PATH
        database.DB_PATH = Path(self.temp_dir.name) / "test.db"
        database.init_db()
        database.insert_chapter(1, "Abdominal Radiology")

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        gc.collect()
        self.temp_dir.cleanup()


class LibraryIsolationTests(TemporaryDatabaseTestCase):
    def _insert_question(self, case_id: int, number: int) -> None:
        question_id = database.insert_question(
            case_id,
            number,
            f"Question {number} with enough text for a test?",
            "multiple_choice",
            ["A", "B", "C", "D", "E"],
            [],
        )
        database.insert_answer(question_id, "", [0, 2], "Explanation", [])

    def test_migration_seeds_cfm_chapter_and_defaults_to_edir(self):
        with database.get_conn() as conn:
            chapter = conn.execute(
                "SELECT title FROM chapters WHERE number=15"
            ).fetchone()
            question_columns = {
                row[1] for row in conn.execute("PRAGMA table_info(questions)")
            }
        self.assertEqual(
            chapter["title"], "UEFA Certificate in Football Management"
        )
        self.assertIn("original_answer_pages", question_columns)
        with database.get_conn() as conn:
            edir_chapter_id = conn.execute(
                "SELECT id FROM chapters WHERE number=1"
            ).fetchone()[0]
        case_id = database.insert_case(
            edir_chapter_id, 1, "", section="mrq", source="EDiR"
        )
        self.assertEqual(database.get_case(case_id)["library_key"], "edir")

    def test_availability_and_sampling_are_library_isolated(self):
        with database.get_conn() as conn:
            edir_chapter_id = conn.execute(
                "SELECT id FROM chapters WHERE number=1"
            ).fetchone()[0]
            cfm_chapter_id = conn.execute(
                "SELECT id FROM chapters WHERE number=15"
            ).fetchone()[0]
        edir_case = database.insert_case(
            edir_chapter_id, 1, "", section="mrq", source="EDiR source"
        )
        cfm_case = database.insert_case(
            cfm_chapter_id,
            1,
            "",
            section="mrq",
            source="Chapter 1 - World football",
            library_key="uefa_cfm",
        )
        for number in range(1, 6):
            self._insert_question(edir_case, number)
            self._insert_question(cfm_case, number)

        cfm_rows = get_availability(library_key="uefa_cfm")
        self.assertEqual({row["source"] for row in cfm_rows}, {"Chapter 1 - World football"})
        config = {
            "version": CONFIG_VERSION,
            "library": "uefa_cfm",
            "ordering": {"mode": "sequential", "section_order": ["mrq"]},
            "sections": {
                "mrq": [
                    {
                        "chapter_id": cfm_chapter_id,
                        "sources": ["Chapter 1 - World football"],
                        "count": 3,
                    }
                ]
            },
        }
        self.assertEqual(validate_config(config), [])
        sampled = sample_config(config, rng=random.Random(7))
        self.assertEqual(len(sampled), 3)
        self.assertEqual({item["source"] for item in sampled}, {"Chapter 1 - World football"})
        self.assertEqual({item["case_id"] for item in sampled}, {cfm_case})

    def test_legacy_config_resolves_to_edir(self):
        self.assertEqual(get_config_library({"version": 2}), "edir")
        uefa_invalid = {
            "version": CONFIG_VERSION,
            "library": "uefa_cfm",
            "ordering": {
                "mode": "sequential",
                "section_order": ["core", "sc", "mrq"],
            },
            "sections": {"core": [], "sc": [], "mrq": []},
        }
        errors = validate_config(uefa_invalid)
        self.assertTrue(any("MRQ only" in error for error in errors))


class CfmValidationTests(unittest.TestCase):
    def setUp(self):
        self.source_pdf = "UEFA-HFM-The-organisation-of-world-football.pdf"
        self.payload = {
            "schema_version": 1,
            "library_key": "uefa_cfm",
            "chapter_number": 15,
            "session_title": "Chapter 1 - The organisation of world football",
            "source_pdf": self.source_pdf,
            "questions": [
                _question(number, self.source_pdf) for number in range(1, 81)
            ],
        }

    def test_valid_eighty_question_session_and_audit(self):
        self.assertEqual(validate_session(self.payload), [])
        audit = audit_session(self.payload)
        self.assertEqual(audit["question_count"], 80)
        self.assertEqual(
            audit["oral_exam_blueprint"],
            {
                "application": {"count": 36, "rate": 0.45},
                "explanation": {"count": 28, "rate": 0.35},
                "factual_anchor": {"count": 16, "rate": 0.2},
            },
        )
        self.assertEqual(audit["correct_answer_counts"], {"1": 20, "2": 20, "3": 20, "4": 20})
        for rate in audit["correct_position_rates"].values():
            self.assertGreaterEqual(rate, 0.30)
            self.assertLessEqual(rate, 0.70)

    def test_validator_rejects_missing_provenance_and_duplicates(self):
        broken = json.loads(json.dumps(self.payload))
        broken["questions"][1]["question_text"] = broken["questions"][0]["question_text"]
        broken["questions"][0]["source_locator"]["pdf_pages"] = []
        errors = validate_session(broken)
        self.assertTrue(any("pdf_pages" in error for error in errors))
        self.assertTrue(any("near-duplicate" in error for error in errors))

    def test_validator_rejects_giveaway_distractor_wording(self):
        broken = json.loads(json.dumps(self.payload))
        correct = set(broken["questions"][0]["answer"]["correct_options"])
        distractor_index = next(index for index in range(5) if index not in correct)
        broken["questions"][0]["options"][distractor_index] = (
            "Every association is automatically guaranteed an identical result."
        )
        errors = validate_session(broken)
        self.assertTrue(any("giveaway absolute" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
