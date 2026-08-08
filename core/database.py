import sqlite3
import json
import os
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(
    os.environ.get(
        "EDIR_PREP_DB_PATH",
        Path(__file__).parent.parent / "data" / "edir_prep.db",
    )
)

LIBRARY_EDIR = "edir"
LIBRARY_UEFA_CFM = "uefa_cfm"
CFM_CHAPTER_NUMBER = 15
CFM_CHAPTER_TITLE = "UEFA Certificate in Football Management"


@contextmanager
def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS chapters (
            id          INTEGER PRIMARY KEY,
            number      INTEGER UNIQUE NOT NULL,
            title       TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cases (
            id                  INTEGER PRIMARY KEY,
            chapter_id          INTEGER NOT NULL,
            case_number         INTEGER NOT NULL,
            section             TEXT NOT NULL DEFAULT 'core',
            clinical_vignette   TEXT,
            library_key         TEXT NOT NULL DEFAULT 'edir',
            FOREIGN KEY (chapter_id) REFERENCES chapters(id)
        );
        CREATE TABLE IF NOT EXISTS questions (
            id              INTEGER PRIMARY KEY,
            case_id         INTEGER NOT NULL,
            q_number        INTEGER NOT NULL,
            question_text   TEXT NOT NULL,
            q_type          TEXT NOT NULL DEFAULT 'free_text',
            options         TEXT,
            page_images     TEXT,
            page_image_captions TEXT,
            source_locator  TEXT,
            original_answer_pages TEXT,
            video_links     TEXT,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        );
        CREATE TABLE IF NOT EXISTS answers (
            id              INTEGER PRIMARY KEY,
            question_id     INTEGER NOT NULL UNIQUE,
            answer_text     TEXT NOT NULL,
            correct_options TEXT,
            explanation     TEXT,
            page_images     TEXT,
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );
        CREATE TABLE IF NOT EXISTS attempts (
            id              INTEGER PRIMARY KEY,
            case_id         INTEGER NOT NULL,
            started_at      REAL NOT NULL,
            submitted_at    REAL,
            time_taken_s    INTEGER,
            timer_limit_s   INTEGER NOT NULL DEFAULT 450,
            FOREIGN KEY (case_id) REFERENCES cases(id)
        );
        CREATE TABLE IF NOT EXISTS question_ratings (
            id          INTEGER PRIMARY KEY,
            attempt_id  INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            rating      TEXT NOT NULL,
            UNIQUE(attempt_id, question_id),
            FOREIGN KEY (attempt_id) REFERENCES attempts(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );
        CREATE TABLE IF NOT EXISTS custom_test_templates (
            id              INTEGER PRIMARY KEY,
            name            TEXT NOT NULL,
            mode            TEXT NOT NULL,
            structure       TEXT NOT NULL DEFAULT 'single',
            timer_limit_s   INTEGER,
            config_json     TEXT NOT NULL,
            created_at      REAL NOT NULL,
            updated_at      REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS custom_tests (
            id               INTEGER PRIMARY KEY,
            template_id      INTEGER,
            name             TEXT NOT NULL,
            mode             TEXT NOT NULL,
            structure        TEXT NOT NULL DEFAULT 'single',
            status           TEXT NOT NULL DEFAULT 'ready',
            timer_limit_s    INTEGER,
            config_json      TEXT NOT NULL,
            current_position INTEGER NOT NULL DEFAULT 0,
            current_phase    INTEGER NOT NULL DEFAULT 0,
            created_at       REAL NOT NULL,
            started_at       REAL,
            submitted_at     REAL,
            time_taken_s     INTEGER,
            FOREIGN KEY (template_id) REFERENCES custom_test_templates(id)
        );
        CREATE TABLE IF NOT EXISTS custom_test_questions (
            id               INTEGER PRIMARY KEY,
            custom_test_id   INTEGER NOT NULL,
            position         INTEGER NOT NULL,
            unit_position    INTEGER NOT NULL,
            phase_index      INTEGER NOT NULL DEFAULT 0,
            section          TEXT NOT NULL,
            case_id          INTEGER NOT NULL,
            question_id      INTEGER NOT NULL,
            source           TEXT NOT NULL,
            chapter_id       INTEGER NOT NULL,
            chapter_number   INTEGER NOT NULL,
            chapter_title    TEXT NOT NULL,
            user_answer      TEXT,
            revealed         INTEGER NOT NULL DEFAULT 0,
            result           TEXT,
            rating           TEXT,
            answered_at      REAL,
            UNIQUE(custom_test_id, position),
            UNIQUE(custom_test_id, question_id),
            FOREIGN KEY (custom_test_id) REFERENCES custom_tests(id),
            FOREIGN KEY (case_id) REFERENCES cases(id),
            FOREIGN KEY (question_id) REFERENCES questions(id),
            FOREIGN KEY (chapter_id) REFERENCES chapters(id)
        );
        CREATE TABLE IF NOT EXISTS custom_test_phases (
            id               INTEGER PRIMARY KEY,
            custom_test_id   INTEGER NOT NULL,
            phase_index      INTEGER NOT NULL,
            section          TEXT NOT NULL,
            name             TEXT NOT NULL,
            timer_limit_s    INTEGER NOT NULL,
            status           TEXT NOT NULL DEFAULT 'ready',
            started_at       REAL,
            submitted_at     REAL,
            time_taken_s     INTEGER,
            UNIQUE(custom_test_id, phase_index),
            FOREIGN KEY (custom_test_id) REFERENCES custom_tests(id)
        );
        CREATE INDEX IF NOT EXISTS idx_custom_tests_status
            ON custom_tests(status, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_custom_test_questions_test
            ON custom_test_questions(custom_test_id, position);
        CREATE INDEX IF NOT EXISTS idx_custom_test_phases_test
            ON custom_test_phases(custom_test_id, phase_index);
        """)
        _migrate(conn)


def _migrate(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info(cases)").fetchall()}
    if "section" not in cols:
        conn.execute("ALTER TABLE cases ADD COLUMN section TEXT NOT NULL DEFAULT 'core'")
    if "source" not in cols:
        conn.execute("ALTER TABLE cases ADD COLUMN source TEXT")
    # Idempotent backfill — runs every startup to cover rows that were NULL
    # because a previous migration run didn't commit the UPDATE.
    conn.execute("UPDATE cases SET source='Essential Guide' WHERE source IS NULL")
    if "chapter_match" not in cols:
        conn.execute("ALTER TABLE cases ADD COLUMN chapter_match TEXT")
    if "original_answer_pages" not in cols:
        conn.execute("ALTER TABLE cases ADD COLUMN original_answer_pages TEXT")
    if "article_summary" not in cols:
        conn.execute("ALTER TABLE cases ADD COLUMN article_summary TEXT")
    if "library_key" not in cols:
        conn.execute(
            "ALTER TABLE cases ADD COLUMN library_key TEXT NOT NULL DEFAULT 'edir'"
        )
    conn.execute(
        "UPDATE cases SET library_key='edir' "
        "WHERE library_key IS NULL OR TRIM(library_key)=''"
    )
    conn.commit()
    cols_q = {r[1] for r in conn.execute("PRAGMA table_info(questions)").fetchall()}
    if "page_image_captions" not in cols_q:
        conn.execute("ALTER TABLE questions ADD COLUMN page_image_captions TEXT")
    if "source_locator" not in cols_q:
        conn.execute("ALTER TABLE questions ADD COLUMN source_locator TEXT")
    if "original_answer_pages" not in cols_q:
        conn.execute("ALTER TABLE questions ADD COLUMN original_answer_pages TEXT")
    if "video_links" not in cols_q:
        conn.execute("ALTER TABLE questions ADD COLUMN video_links TEXT")
    conn.commit()
    conn.execute(
        "INSERT OR IGNORE INTO chapters (number, title) VALUES (?, ?)",
        (CFM_CHAPTER_NUMBER, CFM_CHAPTER_TITLE),
    )
    conn.execute(
        "UPDATE chapters SET title=? WHERE number=?",
        (CFM_CHAPTER_TITLE, CFM_CHAPTER_NUMBER),
    )
    conn.commit()
    cols_templates = {
        r[1] for r in conn.execute("PRAGMA table_info(custom_test_templates)").fetchall()
    }
    if "structure" not in cols_templates:
        conn.execute(
            "ALTER TABLE custom_test_templates "
            "ADD COLUMN structure TEXT NOT NULL DEFAULT 'single'"
        )
    cols_tests = {
        r[1] for r in conn.execute("PRAGMA table_info(custom_tests)").fetchall()
    }
    if "structure" not in cols_tests:
        conn.execute(
            "ALTER TABLE custom_tests "
            "ADD COLUMN structure TEXT NOT NULL DEFAULT 'single'"
        )
    if "current_phase" not in cols_tests:
        conn.execute(
            "ALTER TABLE custom_tests "
            "ADD COLUMN current_phase INTEGER NOT NULL DEFAULT 0"
        )
    cols_custom_q = {
        r[1] for r in conn.execute("PRAGMA table_info(custom_test_questions)").fetchall()
    }
    if "phase_index" not in cols_custom_q:
        conn.execute(
            "ALTER TABLE custom_test_questions "
            "ADD COLUMN phase_index INTEGER NOT NULL DEFAULT 0"
        )
    conn.commit()


def get_next_case_number(chapter_id: int, section: str) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(case_number) FROM cases WHERE chapter_id=? AND section=?",
            (chapter_id, section),
        ).fetchone()
        return (row[0] or 0) + 1


def get_next_q_number(case_id: int) -> int:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(q_number) FROM questions WHERE case_id=?",
            (case_id,),
        ).fetchone()
        return (row[0] or 0) + 1


def has_data():
    try:
        with get_conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM chapters").fetchone()[0] > 0
    except Exception:
        return False


def has_section(section: str, library_key: str = LIBRARY_EDIR) -> bool:
    try:
        with get_conn() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM cases WHERE section=? AND library_key=?",
                (section, library_key),
            ).fetchone()[0] > 0
    except Exception:
        return False


# ── Read queries ──────────────────────────────────────────────────────────────

def get_chapters():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM chapters ORDER BY number").fetchall()


def get_sources(library_key: str = LIBRARY_EDIR) -> list[str]:
    """Return all distinct non-null source values, sorted."""
    try:
        with get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT source FROM cases "
                "WHERE source IS NOT NULL AND library_key=? ORDER BY source",
                (library_key,),
            ).fetchall()
            return [r[0] for r in rows]
    except Exception:
        return []


def get_chapters_with_section(
    section: str,
    source: str | None = None,
    library_key: str = LIBRARY_EDIR,
):
    with get_conn() as conn:
        return conn.execute(
            """SELECT ch.* FROM chapters ch
               WHERE EXISTS (SELECT 1 FROM cases ca
                             WHERE ca.chapter_id=ch.id AND ca.section=?
                             AND ca.library_key=?
                             AND (? IS NULL OR ca.source=?))
               ORDER BY ch.number""",
            (section, library_key, source, source)
        ).fetchall()


def get_cases(
    chapter_id,
    section: str | None = None,
    source: str | None = None,
    library_key: str = LIBRARY_EDIR,
):
    with get_conn() as conn:
        return conn.execute(
            """SELECT * FROM cases WHERE chapter_id=?
               AND library_key=?
               AND (? IS NULL OR section=?)
               AND (? IS NULL OR source=?)
               ORDER BY case_number""",
            (chapter_id, library_key, section, section, source, source)
        ).fetchall()


def get_questions(case_id):
    with get_conn() as conn:
        return conn.execute(
            """SELECT q.*, c.source, c.section, c.library_key,
                      ch.number AS chapter_number, ch.title AS chapter_title
               FROM questions q
               JOIN cases c ON c.id=q.case_id
               JOIN chapters ch ON ch.id=c.chapter_id
               WHERE q.case_id=? ORDER BY q.q_number""",
            (case_id,)
        ).fetchall()


def get_answer(question_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM answers WHERE question_id=?",
            (question_id,)
        ).fetchone()


def get_answers_for_case(case_id):
    with get_conn() as conn:
        return conn.execute(
            """SELECT a.*, q.q_number FROM answers a
               JOIN questions q ON a.question_id = q.id
               WHERE q.case_id=? ORDER BY q.q_number""",
            (case_id,)
        ).fetchall()


def get_case(case_id):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()


def get_case_stats(case_id):
    with get_conn() as conn:
        row = conn.execute(
            """SELECT COUNT(*) as cnt, MAX(submitted_at) as last_at
               FROM attempts WHERE case_id=? AND submitted_at IS NOT NULL""",
            (case_id,)
        ).fetchone()
        return row["cnt"], row["last_at"]


def get_last_ratings(case_id):
    with get_conn() as conn:
        attempt = conn.execute(
            "SELECT id FROM attempts WHERE case_id=? AND submitted_at IS NOT NULL ORDER BY submitted_at DESC LIMIT 1",
            (case_id,)
        ).fetchone()
        if not attempt:
            return {}
        rows = conn.execute(
            "SELECT question_id, rating FROM question_ratings WHERE attempt_id=?",
            (attempt["id"],)
        ).fetchall()
        return {r["question_id"]: r["rating"] for r in rows}


# ── Write queries ─────────────────────────────────────────────────────────────

def insert_chapter(number, title):
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO chapters (number, title) VALUES (?,?)",
            (number, title)
        )
        return conn.execute(
            "SELECT id FROM chapters WHERE number=?", (number,)
        ).fetchone()[0]


def insert_case(
    chapter_id,
    case_number,
    vignette,
    section: str = "core",
    source: str = "Essential Guide",
    chapter_match: str | None = None,
    library_key: str = LIBRARY_EDIR,
):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO cases "
            "(chapter_id, case_number, clinical_vignette, section, source, "
            "chapter_match, library_key) VALUES (?,?,?,?,?,?,?)",
            (
                chapter_id, case_number, vignette, section, source,
                chapter_match, library_key,
            )
        )
        return cur.lastrowid


def insert_question(
    case_id,
    q_number,
    text,
    q_type,
    options,
    page_images,
    page_image_captions=None,
    source_locator=None,
    original_answer_pages=None,
):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO questions
               (case_id, q_number, question_text, q_type, options, page_images,
                page_image_captions, source_locator, original_answer_pages)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                case_id, q_number, text, q_type,
                json.dumps(options) if options else None,
                json.dumps(page_images),
                json.dumps(page_image_captions or [], ensure_ascii=False),
                json.dumps(source_locator, ensure_ascii=False) if source_locator else None,
                json.dumps(original_answer_pages or [], ensure_ascii=False),
            )
        )
        return cur.lastrowid


def insert_answer(question_id, answer_text, correct_options, explanation, page_images):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO answers
               (question_id, answer_text, correct_options, explanation, page_images)
               VALUES (?,?,?,?,?)""",
            (
                question_id, answer_text,
                json.dumps(correct_options) if correct_options else None,
                explanation,
                json.dumps(page_images),
            )
        )


def save_attempt(case_id, started_at, submitted_at, time_taken_s, timer_limit_s):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO attempts
               (case_id, started_at, submitted_at, time_taken_s, timer_limit_s)
               VALUES (?,?,?,?,?)""",
            (case_id, started_at, submitted_at, time_taken_s, timer_limit_s)
        )
        return cur.lastrowid


def save_rating(attempt_id, question_id, rating):
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO question_ratings (attempt_id, question_id, rating)
               VALUES (?,?,?)""",
            (attempt_id, question_id, rating)
        )


def clear_all():
    with get_conn() as conn:
        conn.executescript("""
            DELETE FROM custom_test_phases;
            DELETE FROM custom_test_questions;
            DELETE FROM custom_tests;
            DELETE FROM custom_test_templates;
            DELETE FROM question_ratings;
            DELETE FROM attempts;
            DELETE FROM answers;
            DELETE FROM questions;
            DELETE FROM cases;
            DELETE FROM chapters;
        """)


# ── Admin queries ─────────────────────────────────────────────────────────────

def admin_get_questions(
    section: str | None = None,
    chapter_id: int | None = None,
    source: str | None = None,
    case_number: int | None = None,
    library_key: str | None = None,
):
    with get_conn() as conn:
        return conn.execute(
            """SELECT q.id, q.q_number, q.question_text, q.q_type, q.options,
                      q.page_images, q.page_image_captions, q.source_locator, q.video_links,
                      c.id as case_id, c.case_number, c.section, c.clinical_vignette,
                      c.source, c.library_key,
                      ch.id as chapter_id, ch.number as chapter_number, ch.title as chapter_title
               FROM questions q
               JOIN cases c ON q.case_id = c.id
               JOIN chapters ch ON c.chapter_id = ch.id
               WHERE (c.section = COALESCE(?, c.section))
               AND (c.chapter_id = COALESCE(?, c.chapter_id))
               AND (c.source = COALESCE(?, c.source))
               AND (c.case_number = COALESCE(?, c.case_number))
               AND (c.library_key = COALESCE(?, c.library_key))
               ORDER BY ch.number, c.case_number, q.q_number""",
            (section, chapter_id, source, case_number, library_key),
        ).fetchall()


def admin_update_question(q_id: int, question_text: str, options, page_images: list, video_links: list):
    with get_conn() as conn:
        conn.execute(
            "UPDATE questions SET question_text=?, options=?, page_images=?, video_links=? WHERE id=?",
            (
                question_text,
                json.dumps(options) if options is not None else None,
                json.dumps(page_images),
                json.dumps(video_links),
                q_id,
            ),
        )


def admin_update_answer(
    question_id: int,
    *,
    answer_text: str | None = None,
    correct_options: list | None = None,
    explanation: str | None = None,
    page_images: list | None = None,
):
    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM answers WHERE question_id=?", (question_id,)
        ).fetchone()
        fields, vals = [], []
        if answer_text is not None:
            fields.append("answer_text = ?"); vals.append(answer_text)
        if correct_options is not None:
            fields.append("correct_options = ?"); vals.append(json.dumps(correct_options))
        if explanation is not None:
            fields.append("explanation = ?"); vals.append(explanation)
        if page_images is not None:
            fields.append("page_images = ?"); vals.append(json.dumps(page_images))
        if not fields:
            return
        if existing:
            vals.append(question_id)
            conn.execute(f"UPDATE answers SET {', '.join(fields)} WHERE question_id=?", vals)
        else:
            conn.execute(
                "INSERT INTO answers (question_id, answer_text, correct_options, explanation, page_images) VALUES (?,?,?,?,?)",
                (
                    question_id,
                    answer_text or "",
                    json.dumps(correct_options) if correct_options else None,
                    explanation,
                    json.dumps(page_images) if page_images else None,
                ),
            )


def admin_update_vignette(case_id: int, vignette: str):
    with get_conn() as conn:
        conn.execute("UPDATE cases SET clinical_vignette=? WHERE id=?", (vignette, case_id))


def update_case_original_answer_pages(case_id: int, page_images: list[str]):
    """Store case-level screenshots of the source answer page(s)."""
    with get_conn() as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(cases)").fetchall()}
        if "original_answer_pages" not in cols:
            conn.execute("ALTER TABLE cases ADD COLUMN original_answer_pages TEXT")
        conn.execute(
            "UPDATE cases SET original_answer_pages=? WHERE id=?",
            (json.dumps(page_images), case_id),
        )


def update_case_article_summary(case_id: int, article_summary: str | None):
    """Store a case-level Markdown summary for article-style MRQ sessions."""
    summary = (article_summary or "").strip()
    if not summary:
        return
    with get_conn() as conn:
        cols = {r[1] for r in conn.execute("PRAGMA table_info(cases)").fetchall()}
        if "article_summary" not in cols:
            conn.execute("ALTER TABLE cases ADD COLUMN article_summary TEXT")
        conn.execute(
            "UPDATE cases SET article_summary=? WHERE id=?",
            (summary, case_id),
        )
