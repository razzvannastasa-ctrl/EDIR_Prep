import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "edir_prep.db"


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


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
            clinical_vignette   TEXT,
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
        """)


def has_data():
    try:
        with get_conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM chapters").fetchone()[0] > 0
    except Exception:
        return False


# ── Read queries ─────────────────────────────────────────────────────────────

def get_chapters():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM chapters ORDER BY number").fetchall()


def get_cases(chapter_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM cases WHERE chapter_id=? ORDER BY case_number",
            (chapter_id,)
        ).fetchall()


def get_questions(case_id):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM questions WHERE case_id=? ORDER BY q_number",
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
    """Return (attempt_count, last_submitted_at) for a case."""
    with get_conn() as conn:
        row = conn.execute(
            """SELECT COUNT(*) as cnt, MAX(submitted_at) as last_at
               FROM attempts WHERE case_id=? AND submitted_at IS NOT NULL""",
            (case_id,)
        ).fetchone()
        return row["cnt"], row["last_at"]


def get_last_ratings(case_id):
    """Return {question_id: rating} from the most recent attempt for case_id."""
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


def insert_case(chapter_id, case_number, vignette):
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO cases (chapter_id, case_number, clinical_vignette) VALUES (?,?,?)",
            (chapter_id, case_number, vignette)
        )
        return cur.lastrowid


def insert_question(case_id, q_number, text, q_type, options, page_images):
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO questions
               (case_id, q_number, question_text, q_type, options, page_images)
               VALUES (?,?,?,?,?,?)""",
            (
                case_id, q_number, text, q_type,
                json.dumps(options) if options else None,
                json.dumps(page_images),
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
            DELETE FROM question_ratings;
            DELETE FROM attempts;
            DELETE FROM answers;
            DELETE FROM questions;
            DELETE FROM cases;
            DELETE FROM chapters;
        """)
