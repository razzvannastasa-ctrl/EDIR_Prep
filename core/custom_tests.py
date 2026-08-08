"""Persistence and sampling for mixed, resumable Custom tests."""

from __future__ import annotations

import json
import random
import time
from copy import deepcopy
from collections.abc import Iterable

from core.database import LIBRARY_EDIR, LIBRARY_UEFA_CFM, get_conn
from core.learning import classify_answer


SECTION_ORDER = ("core", "sc", "mrq")
SECTION_LABELS = {"core": "CORE", "sc": "SC", "mrq": "MRQ"}
CONFIG_VERSION = 3
PHASED_CONFIG_VERSION = 2

OFFICIAL_EDIR_CONFIG = {
    "version": CONFIG_VERSION,
    "library": LIBRARY_EDIR,
    "structure": "phased_exam",
    "phases": [
        {
            "phase_index": 0,
            "section": "mrq",
            "name": "MRQs",
            "timer_limit_s": 95 * 60,
            "entries": [
                {"chapter_id": 1, "sources": "*", "count": 9},
                {"chapter_id": 2, "sources": "*", "count": 5},
                {"chapter_id": 3, "sources": "*", "count": 3},
                {"chapter_id": 4, "sources": "*", "count": 8},
                {"chapter_id": 5, "sources": "*", "count": 9},
                {"chapter_id": 6, "sources": "*", "count": 6},
                {"chapter_id": 7, "sources": "*", "count": 6},
                {"chapter_id": 8, "sources": "*", "count": 9},
                {"chapter_id": 9, "sources": "*", "count": 8},
                {"chapter_id": 10, "sources": "*", "count": 5},
                {"chapter_id": 11, "sources": "*", "count": 2},
                {"chapter_id": 12, "sources": "*", "count": 5},
                {"chapter_id": 13, "sources": "*", "count": 2},
                {"chapter_id": 14, "sources": "*", "count": 1},
            ],
        },
        {
            "phase_index": 1,
            "section": "sc",
            "name": "Short Cases",
            "timer_limit_s": 90 * 60,
            "entries": [
                {"chapter_id": 1, "sources": "*", "count": 3},
                {"chapter_id": 2, "sources": "*", "count": 2},
                {"chapter_id": 3, "sources": "*", "count": 1},
                {"chapter_id": 4, "sources": "*", "count": 3},
                {"chapter_id": 5, "sources": "*", "count": 3},
                {"chapter_id": 6, "sources": "*", "count": 2},
                {"chapter_id": 7, "sources": "*", "count": 1},
                {"chapter_id": 8, "sources": "*", "count": 3},
                {"chapter_id": 9, "sources": "*", "count": 3},
                {"chapter_id": 10, "sources": "*", "count": 2},
                {"chapter_id": 14, "sources": "*", "count": 1},
            ],
        },
        {
            "phase_index": 2,
            "section": "core",
            "name": "CORE Cases",
            "timer_limit_s": 90 * 60,
            "entries": [
                {"chapter_id": 1, "sources": "*", "count": 1},
                {"chapter_id": 2, "sources": "*", "count": 1},
                {"chapter_id": 3, "sources": "*", "count": 1},
                {"chapter_id": 4, "sources": "*", "count": 1},
                {"chapter_id": 5, "sources": "*", "count": 1},
                {"chapter_id": 6, "sources": "*", "count": 1},
                {"chapter_id": 8, "sources": "*", "count": 2},
                {"chapter_id": 9, "sources": "*", "count": 1},
                {"chapter_id": 10, "sources": "*", "count": 1},
            ],
        },
    ],
}


def get_official_edir_config() -> dict:
    return deepcopy(OFFICIAL_EDIR_CONFIG)


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def _answer_from_json(value):
    if value is None:
        return None
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


def get_config_library(config: dict | None) -> str:
    """Return a config's library, treating all legacy configs as EDiR."""
    return (config or {}).get("library") or LIBRARY_EDIR


def _library_sections(config: dict | None) -> tuple[str, ...]:
    return ("mrq",) if get_config_library(config) == LIBRARY_UEFA_CFM else SECTION_ORDER


def get_availability(
    section: str | None = None,
    library_key: str = LIBRARY_EDIR,
) -> list[dict]:
    """Return source/chapter availability; unit_count is cases except for MRQs."""
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT c.section, ch.id AS chapter_id, ch.number AS chapter_number,
                      ch.title AS chapter_title, c.source,
                      COUNT(DISTINCT c.id) AS case_count,
                      COUNT(q.id) AS question_count
               FROM cases c
               JOIN chapters ch ON ch.id=c.chapter_id
               JOIN questions q ON q.case_id=c.id
               WHERE (? IS NULL OR c.section=?)
                 AND c.library_key=?
               GROUP BY c.section, ch.id, ch.number, ch.title, c.source
               ORDER BY c.section, ch.number, c.source""",
            (section, section, library_key),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["unit_count"] = (
            item["question_count"] if item["section"] == "mrq" else item["case_count"]
        )
        result.append(item)
    return result


def is_phased_config(config: dict) -> bool:
    return config.get("structure") == "phased_exam"


def get_standard_ordering(config: dict) -> dict:
    """Return a backward-compatible standard-test ordering configuration."""
    ordering = config.get("ordering") or {}
    return {
        "mode": ordering.get("mode", "sequential"),
        "section_order": list(
            ordering.get("section_order") or _library_sections(config)
        ),
    }


def resolve_config_sources(config: dict) -> dict:
    """Resolve '*' source pools at generation time and return a snapshot."""
    resolved = deepcopy(config)
    library_key = get_config_library(resolved)
    availability = get_availability(library_key=library_key)
    source_lookup: dict[tuple[str, int], list[str]] = {}
    for row in availability:
        source_lookup.setdefault((row["section"], row["chapter_id"]), []).append(
            row["source"]
        )
    if is_phased_config(resolved):
        groups = [
            (phase["section"], phase.get("entries", []))
            for phase in resolved.get("phases", [])
        ]
    else:
        groups = [
            (section, resolved.get("sections", {}).get(section, []))
            for section in _library_sections(resolved)
        ]
    for section, entries in groups:
        for entry in entries:
            if entry.get("sources") == "*":
                entry["sources"] = sorted(
                    source_lookup.get((section, int(entry["chapter_id"])), [])
                )
            else:
                entry["sources"] = list(dict.fromkeys(entry.get("sources") or []))
    return resolved


def _config_groups(config: dict) -> list[tuple[str, list[dict]]]:
    if is_phased_config(config):
        return [
            (phase.get("section", ""), phase.get("entries", []))
            for phase in config.get("phases", [])
        ]
    sections = config.get("sections") or {}
    return [
        (section, sections.get(section, []))
        for section in _library_sections(config)
    ]


def validate_config(config: dict) -> list[str]:
    errors: list[str] = []
    total_requested = 0
    library_key = get_config_library(config)
    if library_key not in (LIBRARY_EDIR, LIBRARY_UEFA_CFM):
        errors.append(f"Unknown content library: {library_key}.")
    availability = get_availability(library_key=library_key)
    lookup = {
        (r["section"], r["chapter_id"], r["source"]): r["unit_count"]
        for r in availability
    }

    if is_phased_config(config):
        if library_key != LIBRARY_EDIR:
            errors.append("Phased exams are available only in the EDiR library.")
        phases = config.get("phases") or []
        expected = ["mrq", "sc", "core"]
        actual = [phase.get("section") for phase in phases]
        if actual != expected:
            errors.append("Phased exams must contain MRQ, SC, then CORE phases.")
        for index, phase in enumerate(phases):
            if phase.get("phase_index") != index:
                errors.append("Phased exam indices must be consecutive from zero.")
            if int(phase.get("timer_limit_s") or 0) < 1:
                errors.append(f"{phase.get('name') or 'Phase'} needs a positive timer.")
            if not phase.get("entries"):
                errors.append(f"{phase.get('name') or 'Phase'} needs at least one item.")
    else:
        ordering = get_standard_ordering(config)
        if ordering["mode"] not in ("sequential", "mixed"):
            errors.append("Question ordering must be Sequential or Mixed.")
        expected_sections = _library_sections(config)
        if (
            len(ordering["section_order"]) != len(expected_sections)
            or set(ordering["section_order"]) != set(expected_sections)
        ):
            expected_label = (
                "MRQ only"
                if library_key == LIBRARY_UEFA_CFM
                else "CORE, SC, and MRQ once each"
            )
            errors.append(
                f"Sequential type order must contain {expected_label}."
            )

    for section, entries in _config_groups(config):
        if section not in _library_sections(config):
            errors.append(f"Unknown content type: {section or '(missing)'}.")
            continue
        seen_chapters: set[int] = set()
        for entry in entries:
            chapter_id = int(entry.get("chapter_id") or 0)
            raw_sources = entry.get("sources")
            if raw_sources == "*":
                sources = [
                    row["source"]
                    for row in availability
                    if row["section"] == section and row["chapter_id"] == chapter_id
                ]
            else:
                sources = list(dict.fromkeys(raw_sources or []))
            count = int(entry.get("count") or 0)
            if chapter_id in seen_chapters:
                errors.append(
                    f"{SECTION_LABELS[section]} chapter {chapter_id} is configured more than once."
                )
            seen_chapters.add(chapter_id)
            if not chapter_id or not sources or count < 1:
                errors.append(
                    f"Every {SECTION_LABELS[section]} row needs a chapter, source, and positive amount."
                )
                continue
            available = sum(lookup.get((section, chapter_id, source), 0) for source in sources)
            if count > available:
                errors.append(
                    f"{SECTION_LABELS[section]} chapter {chapter_id}: requested {count}, "
                    f"but only {available} eligible item(s) are available."
                )
            total_requested += count
    if total_requested == 0:
        errors.append("Request at least one CORE case, SC case, or MRQ.")
    return errors


def _eligible_case_ids(
    conn,
    section: str,
    chapter_id: int,
    sources: list[str],
    library_key: str,
) -> list[int]:
    placeholders = ",".join("?" for _ in sources)
    rows = conn.execute(
        f"""SELECT id FROM cases
            WHERE section=? AND chapter_id=? AND library_key=?
              AND source IN ({placeholders})""",
        (section, chapter_id, library_key, *sources),
    ).fetchall()
    return [row["id"] for row in rows]


def _eligible_question_ids(
    conn,
    chapter_id: int,
    sources: list[str],
    library_key: str,
) -> list[int]:
    placeholders = ",".join("?" for _ in sources)
    rows = conn.execute(
        f"""SELECT q.id FROM questions q
            JOIN cases c ON c.id=q.case_id
            WHERE c.section='mrq' AND c.chapter_id=?
              AND c.library_key=?
              AND c.source IN ({placeholders})""",
        (chapter_id, library_key, *sources),
    ).fetchall()
    return [row["id"] for row in rows]


def _question_snapshots(conn, question_ids: Iterable[int]) -> dict[int, dict]:
    ids = list(question_ids)
    if not ids:
        return {}
    placeholders = ",".join("?" for _ in ids)
    rows = conn.execute(
        f"""SELECT q.id AS question_id, q.case_id, c.section, c.source,
                   ch.id AS chapter_id, ch.number AS chapter_number,
                   ch.title AS chapter_title, q.q_number
            FROM questions q
            JOIN cases c ON c.id=q.case_id
            JOIN chapters ch ON ch.id=c.chapter_id
            WHERE q.id IN ({placeholders})""",
        ids,
    ).fetchall()
    return {row["question_id"]: dict(row) for row in rows}


def _spread_mixed_units(
    units_by_section: dict[str, list[tuple[str, int]]],
    rng: random.Random,
) -> list[tuple[int, str, list[tuple[str, int]]]]:
    """Randomly spread each content type across the full unit sequence."""
    ranked_units = []
    for section in SECTION_ORDER:
        units = units_by_section.get(section, [])
        if not units:
            continue
        rng.shuffle(units)
        count = len(units)
        for index, unit in enumerate(units):
            # Stratified random ranks keep minority types distributed instead of
            # allowing all SC/CORE cases to become one accidental block.
            rank = (index + rng.random()) / count
            ranked_units.append((rank, rng.random(), section, unit))
    ranked_units.sort(key=lambda item: (item[0], item[1]))
    return [(0, section, [unit]) for _, _, section, unit in ranked_units]


def sample_config(config: dict, rng: random.Random | None = None) -> list[dict]:
    """Sample once, flatten to ordered questions, and preserve case grouping."""
    config = resolve_config_sources(config)
    errors = validate_config(config)
    if errors:
        raise ValueError("\n".join(errors))
    rng = rng or random.SystemRandom()
    library_key = get_config_library(config)
    phased = is_phased_config(config)
    if phased:
        phase_groups = [
            (
                int(phase["phase_index"]),
                phase["section"],
                phase.get("entries", []),
            )
            for phase in config["phases"]
        ]
    else:
        phase_groups = [
            (0, section, config["sections"].get(section, []))
            for section in _library_sections(config)
        ]

    with get_conn() as conn:
        selected_units: dict[tuple[int, str], list[tuple[str, int]]] = {}
        for phase_index, section, entries in phase_groups:
            units: list[tuple[str, int]] = []
            for entry in entries:
                chapter_id = int(entry["chapter_id"])
                sources = list(entry["sources"])
                count = int(entry["count"])
                if section == "mrq":
                    eligible = _eligible_question_ids(
                        conn, chapter_id, sources, library_key
                    )
                    selected = rng.sample(eligible, count)
                    units.extend(("question", qid) for qid in selected)
                else:
                    eligible = _eligible_case_ids(
                        conn, section, chapter_id, sources, library_key
                    )
                    selected = rng.sample(eligible, count)
                    units.extend(("case", cid) for cid in selected)
            rng.shuffle(units)
            selected_units[(phase_index, section)] = units

        if phased:
            selected_by_group = [
                (
                    int(phase["phase_index"]),
                    phase["section"],
                    selected_units.get(
                        (int(phase["phase_index"]), phase["section"]), []
                    ),
                )
                for phase in config["phases"]
            ]
        else:
            ordering = get_standard_ordering(config)
            if ordering["mode"] == "mixed":
                selected_by_group = _spread_mixed_units(
                    {
                        section: selected_units.get((0, section), [])
                        for section in SECTION_ORDER
                    },
                    rng,
                )
            else:
                selected_by_group = [
                    (0, section, selected_units.get((0, section), []))
                    for section in ordering["section_order"]
                ]

        ordered: list[dict] = []
        unit_position = 0
        for phase_index, section, units in selected_by_group:
            for unit_kind, unit_id in units:
                if unit_kind == "case":
                    q_rows = conn.execute(
                        "SELECT id FROM questions WHERE case_id=? ORDER BY q_number",
                        (unit_id,),
                    ).fetchall()
                    question_ids = [row["id"] for row in q_rows]
                else:
                    question_ids = [unit_id]
                snapshots = _question_snapshots(conn, question_ids)
                for question_id in question_ids:
                    item = snapshots[question_id]
                    item["position"] = len(ordered)
                    item["unit_position"] = unit_position
                    item["phase_index"] = phase_index
                    ordered.append(item)
                unit_position += 1
    return ordered


def save_template(name: str, mode: str, timer_limit_s: int | None, config: dict) -> int:
    errors = validate_config(config)
    if errors:
        raise ValueError("\n".join(errors))
    now = time.time()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO custom_test_templates
               (name, mode, structure, timer_limit_s, config_json, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?)""",
            (
                name.strip(),
                mode,
                config.get("structure", "single"),
                timer_limit_s,
                _json(config),
                now,
                now,
            ),
        )
        return cur.lastrowid


def update_template(
    template_id: int,
    name: str,
    mode: str,
    timer_limit_s: int | None,
    config: dict,
) -> None:
    errors = validate_config(config)
    if errors:
        raise ValueError("\n".join(errors))
    with get_conn() as conn:
        conn.execute(
            """UPDATE custom_test_templates
               SET name=?, mode=?, structure=?, timer_limit_s=?,
                   config_json=?, updated_at=?
               WHERE id=?""",
            (
                name.strip(),
                mode,
                config.get("structure", "single"),
                timer_limit_s,
                _json(config),
                time.time(),
                template_id,
            ),
        )


def get_templates(library_key: str = LIBRARY_EDIR) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM custom_test_templates ORDER BY updated_at DESC, id DESC"
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["config"] = json.loads(item.pop("config_json"))
        if get_config_library(item["config"]) == library_key:
            result.append(item)
    return result


def create_test(
    name: str,
    mode: str,
    timer_limit_s: int | None,
    config: dict,
    *,
    template_id: int | None = None,
    rng: random.Random | None = None,
) -> int:
    resolved_config = resolve_config_sources(config)
    items = sample_config(resolved_config, rng=rng)
    structure = resolved_config.get("structure", "single")
    now = time.time()
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO custom_tests
               (template_id, name, mode, structure, status, timer_limit_s,
                config_json, created_at)
               VALUES (?,?,?,?, 'ready',?,?,?)""",
            (
                template_id,
                name.strip(),
                mode,
                structure,
                timer_limit_s,
                _json(resolved_config),
                now,
            ),
        )
        test_id = cur.lastrowid
        conn.executemany(
            """INSERT INTO custom_test_questions
               (custom_test_id, position, unit_position, phase_index, section, case_id,
                question_id, source, chapter_id, chapter_number, chapter_title)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            [
                (
                    test_id,
                    item["position"],
                    item["unit_position"],
                    item["phase_index"],
                    item["section"],
                    item["case_id"],
                    item["question_id"],
                    item["source"],
                    item["chapter_id"],
                    item["chapter_number"],
                    item["chapter_title"],
                )
                for item in items
            ],
        )
        if structure == "phased_exam":
            conn.executemany(
                """INSERT INTO custom_test_phases
                   (custom_test_id, phase_index, section, name, timer_limit_s, status)
                   VALUES (?,?,?,?,?,'ready')""",
                [
                    (
                        test_id,
                        phase["phase_index"],
                        phase["section"],
                        phase["name"],
                        phase["timer_limit_s"],
                    )
                    for phase in resolved_config["phases"]
                ],
            )
        return test_id


def start_test(test_id: int) -> None:
    now = time.time()
    with get_conn() as conn:
        test = conn.execute(
            "SELECT structure, current_phase FROM custom_tests WHERE id=?",
            (test_id,),
        ).fetchone()
        if not test:
            return
        conn.execute(
            """UPDATE custom_tests
               SET status='in_progress', started_at=COALESCE(started_at, ?)
               WHERE id=? AND status IN ('ready','in_progress')""",
            (now, test_id),
        )
        if test["structure"] == "phased_exam":
            conn.execute(
                """UPDATE custom_test_phases
                   SET status='active', started_at=COALESCE(started_at, ?)
                   WHERE custom_test_id=? AND phase_index=? AND status='ready'""",
                (now, test_id, test["current_phase"]),
            )


def get_test(test_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM custom_tests WHERE id=?", (test_id,)).fetchone()
        if not row:
            return None
        item = dict(row)
        item["config"] = json.loads(item.pop("config_json"))
        item["question_count"] = conn.execute(
            "SELECT COUNT(*) FROM custom_test_questions WHERE custom_test_id=?",
            (test_id,),
        ).fetchone()[0]
        return item


def get_test_phases(test_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT p.*,
                      COUNT(q.id) AS question_count,
                      SUM(CASE WHEN q.result IS NOT NULL OR q.user_answer IS NOT NULL
                               THEN 1 ELSE 0 END) AS completed_count
               FROM custom_test_phases p
               LEFT JOIN custom_test_questions q
                 ON q.custom_test_id=p.custom_test_id
                AND q.phase_index=p.phase_index
               WHERE p.custom_test_id=?
               GROUP BY p.id
               ORDER BY p.phase_index""",
            (test_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_tests(
    statuses: Iterable[str] | None = None,
    library_key: str = LIBRARY_EDIR,
) -> list[dict]:
    params: tuple = ()
    where = ""
    if statuses:
        values = tuple(statuses)
        where = f"WHERE status IN ({','.join('?' for _ in values)})"
        params = values
    with get_conn() as conn:
        rows = conn.execute(
            f"""SELECT t.*,
                       COUNT(ctq.id) AS question_count,
                       SUM(CASE WHEN ctq.result IS NOT NULL OR ctq.user_answer IS NOT NULL
                                THEN 1 ELSE 0 END) AS completed_count
                FROM custom_tests t
                LEFT JOIN custom_test_questions ctq ON ctq.custom_test_id=t.id
                {where}
                GROUP BY t.id
                ORDER BY t.created_at DESC, t.id DESC""",
            params,
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        config = json.loads(item.get("config_json") or "{}")
        if get_config_library(config) == library_key:
            result.append(item)
    return result


def delete_test(test_id: int) -> bool:
    """Delete one custom test and its dedicated saved state."""
    with get_conn() as conn:
        test = conn.execute("SELECT id FROM custom_tests WHERE id=?", (test_id,)).fetchone()
        if not test:
            return False
        conn.execute(
            "DELETE FROM custom_test_phases WHERE custom_test_id=?",
            (test_id,),
        )
        conn.execute(
            "DELETE FROM custom_test_questions WHERE custom_test_id=?",
            (test_id,),
        )
        conn.execute("DELETE FROM custom_tests WHERE id=?", (test_id,))
        return True


def delete_template(template_id: int) -> bool:
    """Delete a saved template while preserving tests generated from its snapshot."""
    with get_conn() as conn:
        template = conn.execute(
            "SELECT id FROM custom_test_templates WHERE id=?",
            (template_id,),
        ).fetchone()
        if not template:
            return False
        conn.execute(
            "UPDATE custom_tests SET template_id=NULL WHERE template_id=?",
            (template_id,),
        )
        conn.execute("DELETE FROM custom_test_templates WHERE id=?", (template_id,))
        return True


def get_test_questions(test_id: int, phase_index: int | None = None) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT ctq.*, q.q_number, q.question_text, q.q_type, q.options,
                      q.page_images, q.page_image_captions, q.source_locator,
                      q.video_links, c.library_key, c.clinical_vignette,
                      COALESCE(q.original_answer_pages, c.original_answer_pages)
                          AS original_answer_pages,
                      c.article_summary
               FROM custom_test_questions ctq
               JOIN questions q ON q.id=ctq.question_id
               JOIN cases c ON c.id=ctq.case_id
               WHERE ctq.custom_test_id=?
                 AND (? IS NULL OR ctq.phase_index=?)
               ORDER BY ctq.position""",
            (test_id, phase_index, phase_index),
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["user_answer_value"] = _answer_from_json(item["user_answer"])
        result.append(item)
    return result


def save_progress(
    test_id: int,
    position: int,
    user_answer,
    *,
    revealed: bool | None = None,
    result: str | None = None,
    rating: str | None = None,
) -> None:
    fields = ["user_answer=?", "answered_at=?"]
    values: list = [_json(user_answer), time.time()]
    if revealed is not None:
        fields.append("revealed=?")
        values.append(int(revealed))
    if result is not None:
        fields.append("result=?")
        values.append(result)
    if rating is not None:
        fields.append("rating=?")
        values.append(rating)
    values.extend((test_id, position))
    with get_conn() as conn:
        conn.execute(
            f"""UPDATE custom_test_questions SET {', '.join(fields)}
                WHERE custom_test_id=? AND position=?""",
            values,
        )
        conn.execute(
            "UPDATE custom_tests SET current_position=? WHERE id=?",
            (position, test_id),
        )


def set_current_position(test_id: int, position: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE custom_tests SET current_position=? WHERE id=?",
            (position, test_id),
        )


def _has_answer(q_type: str, value) -> bool:
    if q_type == "free_text":
        return isinstance(value, str) and bool(value.strip())
    if q_type == "single_choice":
        return isinstance(value, int)
    return bool(value)


def _grade_phase_rows(conn, test_id: int, phase_index: int, *, reveal: bool) -> None:
    rows = conn.execute(
        """SELECT ctq.position, ctq.user_answer, ctq.result,
                  q.q_type, q.options, a.correct_options, a.answer_text
           FROM custom_test_questions ctq
           JOIN questions q ON q.id=ctq.question_id
           LEFT JOIN answers a ON a.question_id=q.id
           WHERE ctq.custom_test_id=? AND ctq.phase_index=?""",
        (test_id, phase_index),
    ).fetchall()
    for row in rows:
        if row["result"] is not None:
            if reveal:
                conn.execute(
                    """UPDATE custom_test_questions SET revealed=1
                       WHERE custom_test_id=? AND position=?""",
                    (test_id, row["position"]),
                )
            continue
        user_answer = _answer_from_json(row["user_answer"])
        if not _has_answer(row["q_type"], user_answer):
            result = "skipped"
        elif row["q_type"] == "free_text":
            result = "unrated"
        else:
            result = classify_answer(
                q_type=row["q_type"],
                user_answer=user_answer,
                options=json.loads(row["options"] or "[]"),
                correct_options=row["correct_options"],
                answer_text=row["answer_text"],
            )
        conn.execute(
            """UPDATE custom_test_questions
               SET revealed=?, result=?
               WHERE custom_test_id=? AND position=?""",
            (int(reveal), result, test_id, row["position"]),
        )


def finish_phase(test_id: int, phase_index: int | None = None) -> None:
    """Complete one phased-exam section without revealing answers before the end."""
    now = time.time()
    with get_conn() as conn:
        test = conn.execute("SELECT * FROM custom_tests WHERE id=?", (test_id,)).fetchone()
        if (
            not test
            or test["structure"] != "phased_exam"
            or test["status"] == "completed"
        ):
            return
        selected_phase = test["current_phase"] if phase_index is None else phase_index
        phase = conn.execute(
            """SELECT * FROM custom_test_phases
               WHERE custom_test_id=? AND phase_index=?""",
            (test_id, selected_phase),
        ).fetchone()
        if not phase or phase["status"] == "completed":
            return

        _grade_phase_rows(conn, test_id, selected_phase, reveal=False)
        started = phase["started_at"] or now
        conn.execute(
            """UPDATE custom_test_phases
               SET status='completed', submitted_at=?, time_taken_s=?
               WHERE custom_test_id=? AND phase_index=?""",
            (now, max(0, int(now - started)), test_id, selected_phase),
        )
        last_phase = conn.execute(
            "SELECT MAX(phase_index) FROM custom_test_phases WHERE custom_test_id=?",
            (test_id,),
        ).fetchone()[0]
        if selected_phase == last_phase:
            conn.execute(
                "UPDATE custom_test_questions SET revealed=1 WHERE custom_test_id=?",
                (test_id,),
            )
            started_test = test["started_at"] or test["created_at"]
            conn.execute(
                """UPDATE custom_tests
                   SET status='completed', submitted_at=?, time_taken_s=?
                   WHERE id=?""",
                (now, max(0, int(now - started_test)), test_id),
            )


def continue_to_next_phase(test_id: int) -> bool:
    """Leave an untimed break and start the next phase. Returns whether it started."""
    now = time.time()
    with get_conn() as conn:
        test = conn.execute("SELECT * FROM custom_tests WHERE id=?", (test_id,)).fetchone()
        if (
            not test
            or test["structure"] != "phased_exam"
            or test["status"] != "in_progress"
        ):
            return False
        current = conn.execute(
            """SELECT * FROM custom_test_phases
               WHERE custom_test_id=? AND phase_index=?""",
            (test_id, test["current_phase"]),
        ).fetchone()
        next_index = test["current_phase"] + 1
        next_phase = conn.execute(
            """SELECT * FROM custom_test_phases
               WHERE custom_test_id=? AND phase_index=?""",
            (test_id, next_index),
        ).fetchone()
        if not current or current["status"] != "completed" or not next_phase:
            return False
        if next_phase["status"] != "ready":
            return False
        first_position = conn.execute(
            """SELECT MIN(position) FROM custom_test_questions
               WHERE custom_test_id=? AND phase_index=?""",
            (test_id, next_index),
        ).fetchone()[0]
        conn.execute(
            """UPDATE custom_test_phases
               SET status='active', started_at=?
               WHERE custom_test_id=? AND phase_index=?""",
            (now, test_id, next_index),
        )
        conn.execute(
            """UPDATE custom_tests
               SET current_phase=?, current_position=?
               WHERE id=?""",
            (next_index, first_position or 0, test_id),
        )
        return True


def finish_test(test_id: int) -> None:
    """Complete an exam/learning test, grading any unrevealed exam questions."""
    now = time.time()
    with get_conn() as conn:
        test = conn.execute("SELECT * FROM custom_tests WHERE id=?", (test_id,)).fetchone()
        if not test or test["status"] == "completed":
            return
        if test["structure"] == "phased_exam":
            phase_index = test["current_phase"]
            # End the transaction before the phase helper opens its own connection.
            conn.commit()
            finish_phase(test_id, phase_index)
            return
        rows = conn.execute(
            """SELECT ctq.position, ctq.user_answer, ctq.result,
                      q.q_type, q.options, a.correct_options, a.answer_text
               FROM custom_test_questions ctq
               JOIN questions q ON q.id=ctq.question_id
               LEFT JOIN answers a ON a.question_id=q.id
               WHERE ctq.custom_test_id=?""",
            (test_id,),
        ).fetchall()
        for row in rows:
            if row["result"] is not None:
                continue
            user_answer = _answer_from_json(row["user_answer"])
            if not _has_answer(row["q_type"], user_answer):
                result = "skipped"
            elif row["q_type"] == "free_text":
                result = "unrated"
            else:
                result = classify_answer(
                    q_type=row["q_type"],
                    user_answer=user_answer,
                    options=json.loads(row["options"] or "[]"),
                    correct_options=row["correct_options"],
                    answer_text=row["answer_text"],
                )
            conn.execute(
                """UPDATE custom_test_questions
                   SET revealed=1, result=? WHERE custom_test_id=? AND position=?""",
                (result, test_id, row["position"]),
            )
        started = test["started_at"] or test["created_at"]
        conn.execute(
            """UPDATE custom_tests
               SET status='completed', submitted_at=?, time_taken_s=?
               WHERE id=?""",
            (now, int(now - started), test_id),
        )


def rate_free_text(test_id: int, position: int, rating: str) -> None:
    result_map = {"got_it": "correct", "partial": "partial", "missed": "incorrect"}
    with get_conn() as conn:
        conn.execute(
            """UPDATE custom_test_questions
               SET rating=?, result=?, revealed=1, answered_at=?
               WHERE custom_test_id=? AND position=?""",
            (rating, result_map[rating], time.time(), test_id, position),
        )


def get_result_breakdown(test_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT phase_index, section, source, result, COUNT(*) AS count
               FROM custom_test_questions
               WHERE custom_test_id=?
               GROUP BY phase_index, section, source, result
               ORDER BY phase_index, section, source, result""",
            (test_id,),
        ).fetchall()
    return [dict(row) for row in rows]
