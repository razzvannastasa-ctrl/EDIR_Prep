import time
import json
import html
import datetime
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from core.database import (
    init_db, has_data, has_section,
    get_sources, get_chapters, get_chapters_with_section, get_cases, get_case, get_questions,
    get_answer, get_answers_for_case,
    get_case_stats, get_last_ratings,
    save_attempt, save_rating,
    insert_case, insert_question, insert_answer,
    get_next_case_number, get_next_q_number,
    admin_get_questions, admin_update_question, admin_update_answer, admin_update_vignette,
    DB_PATH, LIBRARY_EDIR, LIBRARY_UEFA_CFM,
)
from core.learning import classify_answer, correct_option_indices, mrq_score
from core.modality import MODALITIES
from core.custom_tests import (
    CONFIG_VERSION,
    SECTION_LABELS,
    SECTION_ORDER,
    continue_to_next_phase as continue_custom_phase,
    create_test as create_custom_test,
    delete_template as delete_custom_template,
    delete_test as delete_custom_test,
    finish_phase as finish_custom_phase,
    finish_test as finish_custom_test,
    get_availability as get_custom_availability,
    get_official_edir_config,
    get_phase_scores as get_custom_phase_scores,
    score_core_case,
    get_result_breakdown as get_custom_result_breakdown,
    get_standard_ordering as get_custom_ordering,
    get_templates as get_custom_templates,
    get_test as get_custom_test,
    get_test_phases as get_custom_test_phases,
    get_test_questions as get_custom_test_questions,
    get_tests as get_custom_tests,
    is_phased_config,
    pause_phase as pause_custom_phase,
    pause_test as pause_custom_test,
    rate_free_text as rate_custom_free_text,
    resume_phase as resume_custom_phase,
    resume_test as resume_custom_test,
    save_progress as save_custom_progress,
    save_template as save_custom_template,
    set_current_position as set_custom_position,
    start_test as start_custom_test,
    update_template as update_custom_template,
    validate_config as validate_custom_config,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="EDiR Prep",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS: pink sidebar, no top padding ─────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background-color: #C2185B;
}
[data-testid="stSidebar"] * {
    color: white !important;
}
[data-testid="stSidebar"] .stRadio > div {
    gap: 0.2rem;
}
[data-testid="stSidebar"] .stRadio label span {
    color: white !important;
}
[data-testid="stSidebar"] .stButton > button {
    background-color: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.35);
    color: white !important;
    border-radius: 6px;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background-color: rgba(255,255,255,0.28);
    border-color: rgba(255,255,255,0.6);
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.25) !important;
}
.block-container { padding-top: 1.5rem; }
/* Rating buttons */
div[data-testid="column"] .stButton > button[data-got_it] { background:#2E7D32; color:white; }
</style>
""", unsafe_allow_html=True)

# ── DB init ───────────────────────────────────────────────────────────────────
init_db()

# ── Session-state defaults ────────────────────────────────────────────────────
_DEFAULTS = {
    "library_key":    LIBRARY_EDIR,
    "section":        "core_cases",   # core_cases | short_cases | mrqs | custom
    "core_view":      "chapters",     # chapters | cases | start | question | review | learning_summary
    "ch_id":          None,
    "ch_title":       "",
    "case_id":        None,
    "questions":      [],
    "q_index":        0,
    "user_answers":   {},             # {q_id: value}
    "timer_start":    None,
    "timer_limit_s":  450,            # 7.5 min default
    "case_active":    False,
    "attempt_id":     None,
    "ratings":        {},             # {q_id: 'got_it'|'partial'|'missed'}
    "case_vignette":  "",
    "mrq_mode":       "exam",         # exam | learning
    "attempt_mode":   "exam",         # mode locked in when an attempt starts
    "learning_submitted": [],          # question ids with locked answers
    "learning_results":   {},          # {q_id: correct|partial|incorrect|skipped}
    "custom_view":     "dashboard",    # dashboard | test | review | summary
    "custom_test_id":  None,
    "custom_phase_editor": None,
    "custom_phase_editor_nonce": 0,
    "custom_delete_test_id": None,
    "custom_delete_template_id": None,
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Helpers ───────────────────────────────────────────────────────────────────

def _db_section() -> str:
    return {"core_cases": "core", "short_cases": "sc", "mrqs": "mrq"}.get(
        st.session_state.section, "core"
    )


def _library_key() -> str:
    return st.session_state.get("library_key", LIBRARY_EDIR)


def _library_label() -> str:
    return "UEFA CFM" if _library_key() == LIBRARY_UEFA_CFM else "EDiR"


def _section_label() -> str:
    return {"core_cases": "CORE Cases", "short_cases": "Short Cases", "mrqs": "MRQs"}.get(
        st.session_state.section, "CORE Cases"
    )


def _source_locator(value) -> dict:
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {}
    except (TypeError, json.JSONDecodeError):
        return {}


def _render_source_citation(question: dict) -> None:
    locator = _source_locator(question.get("source_locator"))
    if not locator:
        return
    parts = [str(locator.get("file") or question.get("source") or "Source")]
    pdf_pages = locator.get("pdf_pages") or []
    handbook_pages = locator.get("handbook_pages") or []
    book_pages = locator.get("book_pages") or []
    if pdf_pages:
        parts.append("PDF " + ", ".join(f"p. {page}" for page in pdf_pages))
    if handbook_pages:
        parts.append(
            "handbook " + ", ".join(f"p. {page}" for page in handbook_pages)
        )
    if book_pages:
        parts.append("book " + ", ".join(f"p. {page}" for page in book_pages))
    st.caption("Source: " + " · ".join(parts))


def _render_original_answer_page(question: dict) -> None:
    """Show verified source pages only after feedback is available."""
    original_answer_pages = _load_images(
        question.get("original_answer_pages"), crops_only=False
    )
    if original_answer_pages:
        with st.expander("Original answer page", expanded=False):
            _show_images(original_answer_pages, small=True)


def _fmt_time(seconds: float) -> str:
    m, s = int(seconds // 60), int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def _submit_case(next_view: str = "review"):
    now = time.time()
    elapsed = now - st.session_state.timer_start
    aid = save_attempt(
        st.session_state.case_id,
        st.session_state.timer_start,
        now,
        int(elapsed),
        st.session_state.timer_limit_s,
    )
    st.session_state.attempt_id = aid
    if st.session_state.get("attempt_mode") == "learning":
        rating_map = {
            "correct": "got_it",
            "partial": "partial",
            "incorrect": "missed",
            "skipped": "missed",
        }
        for question_id, result in st.session_state.learning_results.items():
            rating = rating_map[result]
            st.session_state.ratings[question_id] = rating
            save_rating(aid, question_id, rating)
    st.session_state.case_active = False
    st.session_state.core_view = next_view


def _render_js_countdown(slot, remaining_seconds: float, *, label: str, ticking: bool) -> None:
    """Render a countdown that ticks entirely client-side (via a components.html
    iframe), so per-second updates need no server round trip at all. This is
    both smoother (no rerun-driven flash) and sidesteps a Streamlit limitation
    where an auto-refreshing @st.fragment cannot write into the sidebar.
    `remaining_seconds` only needs to be fresh as of "now" — the browser owns
    the visible ticking between real reruns. Pass ticking=False to freeze the
    display (e.g. while paused) without starting the JS interval.
    """
    total = max(0, int(round(remaining_seconds)))
    tick_js = (
        f"const t = setInterval(function() {{ r -= 1; draw(); "
        f"if (r <= 0) clearInterval(t); }}, 1000);"
        if ticking else ""
    )
    with slot.container():
        components.html(
            f"""
            <html><head><style>
            html,body{{background:transparent;margin:0;padding:0;
              font-family:"Source Sans Pro",sans-serif;overflow:hidden}}
            </style></head><body>
            <div style="text-align:center">
              <p style="color:rgba(255,255,255,0.75);margin:0;font-size:0.75em;
                letter-spacing:1px">{html.escape(label)}</p>
              <p id="d" style="font-size:3em;font-weight:bold;margin:0;line-height:1;
                color:#FFFFFF"></p>
            </div>
            <script>
              let r = {total};
              const el = document.getElementById('d');
              function draw() {{
                const rr = Math.max(0, r);
                const m = String(Math.floor(rr/60)).padStart(2,'0');
                const s = String(rr%60).padStart(2,'0');
                el.textContent = m+':'+s;
              }}
              draw();
              {tick_js}
            </script>
            </body></html>
            """,
            height=95,
        )


@st.fragment(run_every=1)
def _watch_case_timer_expiry():
    """Poll for exam time-up in isolation, without touching the sidebar (see
    _render_js_countdown). Renders nothing until time actually expires, so
    there is nothing for these per-second ticks to visibly flash."""
    if not (
        st.session_state.case_active
        and st.session_state.timer_start is not None
        and st.session_state.get("attempt_mode") != "learning"
    ):
        return
    elapsed = time.time() - st.session_state.timer_start
    remaining = max(0.0, st.session_state.timer_limit_s - elapsed)
    if remaining <= 0:
        st.warning("Time's up! Submitting automatically…")
        _submit_case()
        st.rerun()


@st.fragment(run_every=1)
def _watch_phase_timer_expiry(test_id: int, phase_index: int, is_last_phase: bool):
    """Poll for exam-phase time-up in isolation (see _watch_case_timer_expiry)."""
    phase = get_custom_test_phases(test_id)[phase_index]
    if phase.get("paused_at"):
        return
    started_at = phase["started_at"] or time.time()
    remaining = max(0.0, phase["timer_limit_s"] - (time.time() - started_at))
    if remaining <= 0:
        finish_custom_phase(test_id, phase_index)
        if is_last_phase:
            st.session_state.custom_view = "review"
        st.rerun()


def _render_phase_pause_button(test_id: int, phase_index: int, paused_at) -> None:
    """Render the pause/resume control below the phase timer."""
    with st.sidebar:
        if paused_at:
            if st.button(
                "▶ Resume timer",
                key=f"resume_phase_{test_id}_{phase_index}",
                use_container_width=True,
            ):
                resume_custom_phase(test_id, phase_index)
                st.rerun()
        elif st.button(
            "⏸ Pause timer",
            key=f"pause_phase_{test_id}_{phase_index}",
            use_container_width=True,
        ):
            pause_custom_phase(test_id, phase_index)
            st.rerun()


@st.fragment(run_every=1)
def _watch_custom_test_timer_expiry(test_id: int):
    """Poll for standalone-test time-up in isolation (see _watch_case_timer_expiry)."""
    test = get_custom_test(test_id)
    if test.get("paused_at"):
        return
    remaining = max(0.0, test["timer_limit_s"] - (time.time() - test["started_at"]))
    if remaining <= 0:
        finish_custom_test(test_id)
        st.session_state.custom_view = "review"
        st.rerun()


def _render_custom_test_pause_button(test_id: int, paused_at) -> None:
    """Render the pause/resume control below the timer."""
    with st.sidebar:
        if paused_at:
            if st.button(
                "▶ Resume timer",
                key=f"resume_test_{test_id}",
                use_container_width=True,
            ):
                resume_custom_test(test_id)
                st.rerun()
        elif st.button(
            "⏸ Pause timer",
            key=f"pause_test_{test_id}",
            use_container_width=True,
        ):
            pause_custom_test(test_id)
            st.rerun()


_APP_DIR = Path(__file__).parent

def _load_images(paths_json: str | None, *, crops_only: bool = True) -> list[Path]:
    if not paths_json:
        return []
    try:
        paths = []
        for p in json.loads(paths_json):
            if crops_only and "crops" not in p:
                continue  # skip full-page fallbacks, only show cropped clinical images
            pp = Path(p)
            if not pp.is_absolute():
                pp = _APP_DIR / pp
            paths.append(pp)
        return paths
    except Exception:
        return []


def _load_image_captions(value) -> list[str]:
    try:
        captions = json.loads(value or "[]") if isinstance(value, str) else value
        return [str(caption) for caption in captions] if isinstance(captions, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def _show_images(
    paths: list[Path],
    caption: str = "",
    small: bool = False,
    captions: list[str] | None = None,
    grid_cols: int = 1,
):
    captions = captions or []

    def _caption_for(index: int) -> str:
        return (
            captions[index]
            if index < len(captions) and captions[index]
            else caption if index == 0 else ""
        )

    if grid_cols > 1 and paths:
        n_cols = min(grid_cols, len(paths))
        # Use spacer columns to shrink the image's rendered width while still
        # handing the browser the full-resolution file (so the fullscreen
        # expand shows it at native quality, not a downscaled version).
        cols = st.columns(n_cols * 2) if small else st.columns(n_cols)
        for index, p in enumerate(paths):
            col = cols[(index % n_cols) * 2] if small else cols[index % n_cols]
            if p.exists():
                col.image(str(p), use_container_width=True, caption=_caption_for(index))
            else:
                col.caption(f"Image not rendered yet: {p.name}")
        return

    for index, p in enumerate(paths):
        image_caption = _caption_for(index)
        if p.exists():
            if small:
                col, _ = st.columns([1, 3])
                col.image(str(p), use_container_width=True, caption=image_caption)
            else:
                st.image(str(p), use_container_width=True, caption=image_caption)
        else:
            st.caption(f"Image not rendered yet: {p.name}")


def _has_user_answer(q_type: str, user_answer) -> bool:
    if q_type == "free_text":
        return bool((user_answer or "").strip())
    if q_type == "single_choice":
        return isinstance(user_answer, int)
    if q_type == "multiple_choice":
        return bool(user_answer)
    return False


def _submit_learning_answer(q: dict, options: list[str], *, skipped: bool = False):
    q_id = q["id"]
    if q_id in st.session_state.learning_submitted:
        return
    ans_row = get_answer(q_id)
    result = classify_answer(
        q_type=q["q_type"],
        user_answer=st.session_state.user_answers.get(q_id),
        options=options,
        correct_options=ans_row["correct_options"] if ans_row else None,
        answer_text=ans_row["answer_text"] if ans_row else None,
        skipped=skipped,
    )
    st.session_state.learning_submitted.append(q_id)
    st.session_state.learning_results[q_id] = result


def _show_learning_feedback(q: dict, options: list[str]):
    q_id = q["id"]
    result = st.session_state.learning_results[q_id]
    feedback = {
        "correct": (st.success, "Correct"),
        "partial": (st.warning, "Partially correct"),
        "incorrect": (st.error, "Incorrect"),
        "skipped": (st.info, "Skipped"),
    }
    message_fn, label = feedback[result]
    message_fn(label)

    correct_indices = _correct_indices_for(q_id, options)
    user_answer = st.session_state.user_answers.get(q_id)

    st.markdown(_your_answer_heading(q["q_type"], user_answer, correct_indices, len(options)))
    if q["q_type"] == "free_text":
        _render_free_text_answer(user_answer)
        st.markdown("**Correct answer**")
    else:
        _render_choice_feedback_grid(options, user_answer, correct_indices)

    _render_correct_answer(
        q_id, options, collapse_explanation=True, question=q,
        show_correct_text=(q["q_type"] == "free_text"),
    )


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Prep Library")
    _library_labels = ["EDiR", "UEFA CFM"]
    _library_keys = [LIBRARY_EDIR, LIBRARY_UEFA_CFM]
    _library_index = _library_keys.index(_library_key())
    _library_choice = st.radio(
        "Library", _library_labels, index=_library_index, horizontal=True
    )
    _chosen_library = _library_keys[_library_labels.index(_library_choice)]
    if _chosen_library != _library_key():
        st.session_state.library_key = _chosen_library
        st.session_state.section = (
            "mrqs" if _chosen_library == LIBRARY_UEFA_CFM else "core_cases"
        )
        st.session_state.core_view = "chapters"
        st.session_state.custom_view = "dashboard"
        st.session_state.custom_phase_editor = None
        st.session_state.custom_test_id = None
        st.session_state.study_source = None
        st.session_state.mrq_mode = (
            "learning" if _chosen_library == LIBRARY_UEFA_CFM else "exam"
        )
        st.session_state.case_active = False
        st.rerun()
    st.markdown("---")

    if _library_key() == LIBRARY_UEFA_CFM:
        _menu_labels = ["MRQs", "Custom"]
        _menu_keys = ["mrqs", "custom"]
    else:
        _menu_labels = ["CORE Cases", "Short Cases", "MRQs", "Custom"]
        _menu_keys = ["core_cases", "short_cases", "mrqs", "custom"]
    if st.session_state.section not in _menu_keys:
        st.session_state.section = "core_cases"
        st.session_state.core_view = "chapters"
    _current_idx = _menu_keys.index(st.session_state.section)

    _choice = st.radio("Navigation", _menu_labels, index=_current_idx, label_visibility="collapsed")
    _chosen_key = _menu_keys[_menu_labels.index(_choice)]

    if _chosen_key != st.session_state.section:
        st.session_state.section = _chosen_key
        if _chosen_key == "custom":
            st.session_state.custom_view = "dashboard"
        else:
            st.session_state.core_view = "chapters"
        st.rerun()

    st.markdown("---")

    # Timer slot — filled later if case is active
    _timer_slot = st.empty()

# ── Timer display (client-side ticking, no per-second rerun) ─────────────────
if (
    st.session_state.case_active
    and st.session_state.timer_start is not None
    and st.session_state.get("attempt_mode") != "learning"
):
    _case_elapsed = time.time() - st.session_state.timer_start
    _case_remaining = max(0.0, st.session_state.timer_limit_s - _case_elapsed)
    with st.sidebar:
        _render_js_countdown(
            _timer_slot, _case_remaining, label="TIME REMAINING", ticking=True
        )
# Isolated fragment that only watches for time-up; kept out of the sidebar
# (a @st.fragment cannot write to the sidebar in this Streamlit version).
_watch_case_timer_expiry()


# ══════════════════════════════════════════════════════════════════════════════
# VIEW FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def view_chapters():
    label = _section_label()
    sec   = _db_section()
    st.header(
        "UEFA Certificate in Football Management"
        if _library_key() == LIBRARY_UEFA_CFM
        else label
    )

    if not has_section(sec, _library_key()):
        st.info(f"No {label} content is currently available.")
        return

    # Source filter (shown whenever at least one source exists)
    sources = get_sources(_library_key())
    if sources and _library_key() == LIBRARY_EDIR:
        src_opts  = ["All sources"] + sources
        src_label = st.selectbox("Source", src_opts, key="study_source_sel")
        st.session_state["study_source"] = None if src_label == "All sources" else src_label
    else:
        st.session_state["study_source"] = None
    src = st.session_state.get("study_source")

    chapters = get_chapters_with_section(
        sec, source=src, library_key=_library_key()
    )
    cols_per_row = 3

    for row_start in range(0, len(chapters), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, ch in zip(cols, chapters[row_start: row_start + cols_per_row]):
            n_cases = len(
                get_cases(
                    ch["id"], section=sec, source=src,
                    library_key=_library_key(),
                )
            )
            if sec == "mrq":
                count_label = "MRQ session" if n_cases == 1 else "MRQ sessions"
            elif sec == "sc":
                count_label = "Short Case" if n_cases == 1 else "Short Cases"
            else:
                count_label = "CORE case" if n_cases == 1 else "CORE cases"
            with col:
                with st.container(border=True):
                    st.markdown(f"**Chapter {ch['number']}**")
                    st.markdown(f"### {ch['title']}")
                    st.caption(f"{n_cases} {count_label}")
                    if st.button("Open →", key=f"open_ch_{ch['id']}_{sec}",
                                 use_container_width=True):
                        st.session_state.ch_id    = ch["id"]
                        st.session_state.ch_title = ch["title"]
                        st.session_state.core_view = "cases"
                        st.rerun()


def view_cases():
    if st.button("← Chapters"):
        st.session_state.core_view = "chapters"
        st.rerun()

    sec   = _db_section()
    label = _section_label()
    st.header(f"{label} — {st.session_state.ch_title}")
    src   = st.session_state.get("study_source")
    cases = get_cases(
        st.session_state.ch_id,
        section=sec,
        source=src,
        library_key=_library_key(),
    )

    if not cases:
        st.warning("No cases found for this chapter.")
        return

    for case in cases:
        attempts, last_at = get_case_stats(case["id"])
        last_ratings = get_last_ratings(case["id"])

        with st.container(border=True):
            c_info, c_btn = st.columns([4, 1])

            with c_info:
                if sec == "mrq":
                    n_qs = len(get_questions(case["id"]))
                    if _library_key() == LIBRARY_UEFA_CFM:
                        st.markdown(f"**{case['source']}**")
                        st.caption(
                            f"Complete handbook session · {n_qs} multiple-response "
                            f"question{'s' if n_qs != 1 else ''}"
                        )
                    else:
                        st.markdown(
                            f"**MRQ Session — Chapter {st.session_state.ch_title}**"
                        )
                        st.caption(
                            f"{n_qs} multiple-choice question"
                            f"{'s' if n_qs != 1 else ''}"
                        )
                else:
                    st.markdown(f"**Case {case['case_number']}**")
                    vig = (case["clinical_vignette"] or "").strip()
                    preview = vig[:140] + ("…" if len(vig) > 140 else "")
                    st.caption(preview or "_No vignette available_")

                if attempts:
                    last_str = datetime.datetime.fromtimestamp(last_at).strftime("%d %b %Y")
                    if last_ratings:
                        got = sum(1 for r in last_ratings.values() if r == "got_it")
                        par = sum(1 for r in last_ratings.values() if r == "partial")
                        mis = sum(1 for r in last_ratings.values() if r == "missed")
                        badge = f"✓{got} ~{par} ✗{mis}"
                    else:
                        badge = ""
                    st.caption(f"Attempted {attempts}×  •  Last: {last_str}  {badge}")

            with c_btn:
                if st.button("Start", key=f"start_case_{case['id']}",
                             use_container_width=True, type="primary"):
                    st.session_state.case_id   = case["id"]
                    st.session_state.core_view = "start"
                    st.rerun()


def view_case_start():
    if st.button("← Cases"):
        st.session_state.core_view = "cases"
        st.rerun()

    sec       = _db_section()
    case      = get_case(st.session_state.case_id)
    questions = get_questions(st.session_state.case_id)
    n_q       = len(questions)

    if sec == "mrq":
        st.header(
            f"{case['source']} — MRQs"
            if _library_key() == LIBRARY_UEFA_CFM
            else f"MRQs — Chapter {st.session_state.ch_title}"
        )
    else:
        st.header(f"Case {case['case_number']}  —  {st.session_state.ch_title}")

    if sec == "mrq":
        st.radio(
            "Study mode",
            ["exam", "learning"],
            format_func=lambda mode: "Exam mode" if mode == "exam" else "Learning mode",
            horizontal=True,
            key="mrq_mode",
        )

    is_learning = sec == "mrq" and st.session_state.mrq_mode == "learning"
    if is_learning:
        st.markdown(
            f"**{n_q} question{'s' if n_q != 1 else ''}** — untimed. "
            "Check each answer to see immediate feedback before continuing."
        )
    else:
        st.markdown(
            f"**{n_q} question{'s' if n_q != 1 else ''}** — "
            "work through all before time runs out."
        )

    st.markdown("---")
    c_timer, c_start = st.columns([1, 2])
    with c_timer:
        if is_learning:
            st.info("Untimed session")
        else:
            new_limit = st.number_input(
                "Time limit (min)", min_value=1,
                max_value=180 if _library_key() == LIBRARY_UEFA_CFM else 60,
                value=st.session_state.timer_limit_s // 60, step=1,
            )
            st.session_state.timer_limit_s = int(new_limit * 60)
    with c_start:
        st.markdown("<br>", unsafe_allow_html=True)
        start_label = "▶  Start Learning" if is_learning else "▶  Start Case"
        if st.button(start_label, type="primary", use_container_width=True):
            st.session_state.questions        = [dict(q) for q in questions]
            st.session_state.q_index          = 0
            st.session_state.user_answers     = {}
            st.session_state.timer_start      = time.time()
            st.session_state.case_active      = True
            st.session_state.ratings          = {}
            st.session_state.attempt_id       = None
            st.session_state.attempt_mode     = "learning" if is_learning else "exam"
            st.session_state.learning_submitted = []
            st.session_state.learning_results   = {}
            st.session_state.core_view        = "question"
            st.session_state.case_vignette    = (case["clinical_vignette"] or "").strip()
            st.rerun()


def view_question():
    is_learning = (
        _db_section() == "mrq"
        and st.session_state.get("attempt_mode") == "learning"
    )
    # Countdown ticking and time's-up auto-submit are handled by the sidebar's
    # _tick_case_timer fragment, so this view doesn't need its own rerun timer.

    questions = st.session_state.questions
    q_idx     = st.session_state.q_index
    n_q       = len(questions)

    if not questions:
        st.error("No questions loaded.")
        return

    q    = questions[q_idx]
    q_id = q["id"]
    is_submitted = q_id in st.session_state.learning_submitted

    # Progress bar
    st.progress((q_idx + 1) / n_q,
                text=f"Question {q_idx + 1} of {n_q}")

    col_q, col_img = st.columns([1, 1], gap="large")

    # ── Left: question + answer input ─────────────────────────────────────────
    with col_q:
        sec = _db_section()
        if q_idx == 0 and sec != "mrq":
            vig = st.session_state.get("case_vignette", "")
            if vig:
                st.info(vig)
        st.markdown(f"### Q{q['q_number']}")
        if is_learning and q.get("source"):
            # Hidden in exam mode — seeing the source book can hint at the answer.
            st.caption(
                f"{q['source']} · Chapter {q['chapter_number']}: "
                f"{q['chapter_title']} · {SECTION_LABELS.get(sec, sec.upper())}"
            )
        st.markdown(q["question_text"])

        q_type  = q["q_type"]
        saved   = st.session_state.user_answers.get(q_id)
        options = json.loads(q["options"]) if q.get("options") else []

        if not (is_learning and is_submitted):
            if q_type == "free_text":
                val = st.text_area(
                    "Your answer",
                    value=saved or "",
                    height=160,
                    placeholder="Write your answer here…",
                    key=f"ft_{q_id}",
                )
                st.session_state.user_answers[q_id] = val

            elif q_type == "single_choice":
                prev_idx = saved if isinstance(saved, int) and saved < len(options) else None
                choice = st.radio(
                    "Select one:",
                    options,
                    index=prev_idx,
                    key=f"sc_{q_id}",
                )
                if choice in options:
                    st.session_state.user_answers[q_id] = options.index(choice)

            elif q_type == "multiple_choice":
                prev_sel = saved if isinstance(saved, list) else []
                st.caption("Select all that apply:")
                chosen = _render_mc_checkbox_input(
                    options, prev_sel, key_prefix=f"mc_{q_id}", disabled=False,
                )
                st.session_state.user_answers[q_id] = chosen

        if is_learning:
            if is_submitted:
                _show_learning_feedback(q, options)

            st.markdown("---")
            if not is_submitted:
                nav = st.columns([1, 2, 1])
                with nav[0]:
                    if q_idx > 0 and st.button("← Previous", use_container_width=True):
                        st.session_state.q_index -= 1
                        st.rerun()
                with nav[1]:
                    can_check = _has_user_answer(
                        q_type, st.session_state.user_answers.get(q_id)
                    )
                    if st.button(
                        "Check answer",
                        type="primary",
                        use_container_width=True,
                        disabled=not can_check,
                    ):
                        _submit_learning_answer(q, options)
                        st.rerun()
                with nav[2]:
                    if st.button("Skip / Show answer", use_container_width=True):
                        _submit_learning_answer(q, options, skipped=True)
                        st.rerun()
            else:
                nav = st.columns([1, 1, 2])
                with nav[0]:
                    if q_idx > 0 and st.button("← Previous", use_container_width=True):
                        st.session_state.q_index -= 1
                        st.rerun()
                with nav[2]:
                    if q_idx < n_q - 1:
                        if st.button(
                            "Next question →", type="primary", use_container_width=True
                        ):
                            st.session_state.q_index += 1
                            st.rerun()
                    elif st.button(
                        "Finish session", type="primary", use_container_width=True
                    ):
                        _submit_case("learning_summary")
                        st.rerun()
        else:
            # Exam-mode navigation
            st.markdown("---")
            nav = st.columns([1, 1, 2])
            with nav[0]:
                if q_idx > 0:
                    if st.button("← Prev", use_container_width=True):
                        st.session_state.q_index -= 1
                        st.rerun()
            with nav[2]:
                if q_idx < n_q - 1:
                    if st.button("Next →", type="primary", use_container_width=True):
                        st.session_state.q_index += 1
                        st.rerun()
                else:
                    if st.button("Submit Case", type="primary", use_container_width=True):
                        _submit_case()
                        st.rerun()

    # ── Right: page images + video links ─────────────────────────────────────
    with col_img:
        imgs = _load_images(q.get("page_images"))
        if imgs:
            _show_images(
                imgs,
                captions=_load_image_captions(q.get("page_image_captions")),
                grid_cols=2,
            )
        video_links = json.loads(q.get("video_links") or "[]")
        for i, url in enumerate(video_links, 1):
            st.markdown(f"[▶ Video {i}]({url})")


def view_learning_summary():
    if st.button("← MRQ sessions"):
        st.session_state.core_view = "cases"
        st.session_state.case_active = False
        st.rerun()

    st.header("Learning session complete")
    results = st.session_state.learning_results
    total = len(st.session_state.questions)
    counts = {
        result: sum(1 for value in results.values() if value == result)
        for result in ("correct", "partial", "incorrect", "skipped")
    }

    metric_cols = st.columns(4)
    metric_cols[0].metric("Correct", counts["correct"])
    metric_cols[1].metric("Partial", counts["partial"])
    metric_cols[2].metric("Incorrect", counts["incorrect"])
    metric_cols[3].metric("Skipped", counts["skipped"])
    st.caption(f"Completed {len(results)} of {total} questions")

    st.markdown("---")
    result_labels = {
        "correct": "Correct",
        "partial": "Partially correct",
        "incorrect": "Incorrect",
        "skipped": "Skipped",
    }
    for q in st.session_state.questions:
        q_id = q["id"]
        result = results.get(q_id)
        options = json.loads(q["options"]) if q.get("options") else []
        ans_row = get_answer(q_id)
        correct_indices = _correct_indices_for(q_id, options)

        with st.expander(
            f"Q{q['q_number']} — {result_labels.get(result, 'Not completed')}",
            expanded=result in ("incorrect", "partial"),
        ):
            st.markdown(q["question_text"])
            user_answer = st.session_state.user_answers.get(q_id)
            if q["q_type"] == "free_text":
                col_a, col_b = st.columns(2, gap="large")
                with col_a:
                    st.markdown("**Your answer**")
                    _render_free_text_answer(user_answer)
                with col_b:
                    st.markdown("**Correct answer**")
                    if ans_row and ans_row["answer_text"]:
                        st.markdown(ans_row["answer_text"])
                    else:
                        st.markdown("_Answer not available_")
            else:
                st.markdown(
                    _your_answer_heading(q["q_type"], user_answer, correct_indices, len(options))
                )
                _render_choice_feedback_grid(options, user_answer, correct_indices)
            if ans_row and ans_row["explanation"]:
                with st.expander("Explanation", expanded=False):
                    st.markdown(ans_row["explanation"])


def view_review():
    c_back, c_title = st.columns([1, 6])
    with c_back:
        if st.button("← Cases"):
            st.session_state.core_view  = "cases"
            st.session_state.case_active = False
            st.rerun()
    with c_title:
        st.header("Review")

    questions  = st.session_state.questions
    attempt_id = st.session_state.attempt_id
    case_row = get_case(st.session_state.case_id)
    article_summary = ""
    if case_row and "article_summary" in case_row.keys():
        article_summary = (case_row["article_summary"] or "").strip()
    original_answer_pages = []
    if _db_section() in ("core", "sc") and case_row and "original_answer_pages" in case_row.keys():
        original_answer_pages = _load_images(case_row["original_answer_pages"], crops_only=False)

    for q in questions:
        q_id     = q["id"]
        ans_row  = get_answer(q_id)
        user_ans = st.session_state.user_answers.get(q_id)
        options  = json.loads(q["options"]) if q.get("options") else []
        rating   = st.session_state.ratings.get(q_id)
        correct_indices = set(
            correct_option_indices(
                options,
                ans_row["correct_options"] if ans_row else None,
                ans_row["answer_text"] if ans_row else None,
            )
        )

        _RATING_COLORS = {
            "got_it":  ("#2E7D32", "✓ Got it"),
            "partial": ("#E65100", "~ Partial"),
            "missed":  ("#C62828", "✗ Missed"),
        }
        r_color, r_label = _RATING_COLORS.get(rating, ("#888", "Not rated"))

        with st.expander(
            f"Q{q['q_number']}   "
            + (f"— **:{r_color}[{r_label}]**" if rating else "— _not rated_"),
            expanded=True,
        ):
            if q.get("source"):
                st.caption(
                    f"{q['source']} · Chapter {q['chapter_number']}: "
                    f"{q['chapter_title']} · "
                    f"{SECTION_LABELS.get(_db_section(), _db_section().upper())}"
                )
            # ── Question + user answer | Correct answer ───────────────────────
            col_q, col_a = st.columns(2, gap="large")

            with col_q:
                st.markdown("**Question**")
                st.markdown(q["question_text"])

                if q["q_type"] == "free_text":
                    st.markdown("**Your answer**")
                    _render_free_text_answer(user_ans)
                elif options:
                    st.markdown(
                        _your_answer_heading(q["q_type"], user_ans, correct_indices, len(options))
                    )
                    _render_choice_feedback_grid(options, user_ans, correct_indices)

            with col_a:
                if q["q_type"] == "free_text":
                    st.markdown("**Correct Answer**")
                    if ans_row and ans_row["answer_text"]:
                        st.markdown(ans_row["answer_text"])
                    else:
                        st.markdown("_Answer not available_")

                if ans_row and ans_row["explanation"]:
                    st.markdown("**Explanation**")
                    st.markdown(ans_row["explanation"])

                _render_source_citation(q)

                answer_imgs = _load_images(ans_row["page_images"] if ans_row else None)
                if answer_imgs:
                    st.markdown("**Answer Images**")
                    _show_images(answer_imgs, small=True, grid_cols=2)

                _render_original_answer_page(q)

            # Cropped clinical images for this question
            imgs = _load_images(q.get("page_images"))
            if imgs:
                _show_images(
                    imgs,
                    small=True,
                    captions=_load_image_captions(q.get("page_image_captions")),
                )

            # Video links
            video_links = json.loads(q.get("video_links") or "[]")
            for i, url in enumerate(video_links, 1):
                st.markdown(f"[▶ Video {i}]({url})")

            # ── Rating buttons ────────────────────────────────────────────────
            st.markdown("---")
            rb1, rb2, rb3 = st.columns(3)

            with rb1:
                btn_style = "primary" if rating == "got_it" else "secondary"
                if st.button("✓ Got it", key=f"got_{q_id}",
                             use_container_width=True, type=btn_style):
                    st.session_state.ratings[q_id] = "got_it"
                    if attempt_id:
                        save_rating(attempt_id, q_id, "got_it")
                    st.rerun()
            with rb2:
                btn_style = "primary" if rating == "partial" else "secondary"
                if st.button("~ Partial", key=f"par_{q_id}",
                             use_container_width=True, type=btn_style):
                    st.session_state.ratings[q_id] = "partial"
                    if attempt_id:
                        save_rating(attempt_id, q_id, "partial")
                    st.rerun()
            with rb3:
                btn_style = "primary" if rating == "missed" else "secondary"
                if st.button("✗ Missed", key=f"mis_{q_id}",
                             use_container_width=True, type=btn_style):
                    st.session_state.ratings[q_id] = "missed"
                    if attempt_id:
                        save_rating(attempt_id, q_id, "missed")
                    st.rerun()

    if article_summary:
        with st.expander("Article summary", expanded=False):
            st.markdown(article_summary)

    if original_answer_pages:
        with st.expander("Original answer page", expanded=False):
            _show_images(original_answer_pages, small=True)


def _custom_default_name(prefix: str = "Custom test") -> str:
    stamp = datetime.datetime.now().strftime("%d %b %Y %H:%M")
    return f"{prefix} — {stamp}"


def _custom_context_label(q: dict) -> str:
    if q.get("library_key") == LIBRARY_UEFA_CFM:
        return f"{q['source']} · UEFA CFM · MRQ"
    return (
        f"{q['source']} · Chapter {q['chapter_number']}: {q['chapter_title']} · "
        f"{SECTION_LABELS[q['section']]}"
    )


def _render_free_text_answer(user_answer):
    st.markdown(user_answer or "_No answer_")


def _render_mc_checkbox_input(
    options: list[str], selected: list[int], *, key_prefix: str, disabled: bool
) -> list[int]:
    """Render multiple_choice options as a checkbox column instead of a dropdown."""
    chosen = []
    for i, option_text in enumerate(options):
        checked = st.checkbox(
            option_text,
            value=i in selected,
            key=f"{key_prefix}_{i}",
            disabled=disabled,
        )
        if checked:
            chosen.append(i)
    return chosen


def _render_choice_feedback_grid(
    options: list[str], user_answer, correct_indices: set[int]
) -> None:
    """Render every option as a bordered row with a correctness mark to its
    left (✔ = objectively correct, ✘ = selected but wrong) and a checked/
    unchecked box coloured green (selected & correct) or red (selected &
    wrong). Used for both single_choice and multiple_choice feedback.
    """
    if isinstance(user_answer, int):
        selected = {user_answer}
    elif isinstance(user_answer, list):
        selected = set(user_answer)
    else:
        selected = set()

    n_correct = len(selected & correct_indices)
    n_wrong = len(selected - correct_indices)
    n_missed = len(correct_indices - selected)
    if selected:
        score = mrq_score(selected, correct_indices, len(options))
        if score >= 1.0:
            icon, color, bg = "✅", "#2E7D32", "rgba(46,125,50,0.08)"
        elif score >= 0.5:
            icon, color, bg = "⚠️", "#E65100", "rgba(230,81,0,0.08)"
        else:
            icon, color, bg = "❌", "#C62828", "rgba(198,40,40,0.08)"
        parts = []
        if n_correct:
            parts.append(
                f"<span style='color:#2E7D32;font-weight:600'>"
                f"{n_correct} correct answer(s)</span>"
            )
        if n_missed:
            parts.append(
                f"<span style='color:#E65100;font-weight:600'>"
                f"{n_missed} missed answer(s)</span>"
            )
        if n_wrong:
            parts.append(
                f"<span style='color:#C62828;font-weight:600'>"
                f"{n_wrong} wrong answer(s)</span>"
            )
        banner = f"{icon} {', '.join(parts)}"
    else:
        color, bg, banner = "#999", "transparent", "No answer selected"
    st.markdown(
        f"<div style='border:1px solid {color};background:{bg};border-radius:6px;"
        f"padding:10px 14px;margin-bottom:10px'>{banner}</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<style>"
        ".edir-mark{width:1em;display:inline-block;font-weight:bold}"
        ".edir-mark.wrong{color:#C62828}"
        ".edir-mark.correct{color:#111}"
        "@media (prefers-color-scheme: dark){"
        ".edir-mark.correct{color:#fff}"
        "}"
        "</style>",
        unsafe_allow_html=True,
    )
    for i, option_text in enumerate(options):
        is_selected = i in selected
        is_correct = i in correct_indices
        if is_correct:
            mark, mark_class = "✔", "correct"
        elif is_selected:
            mark, mark_class = "✘", "wrong"
        else:
            mark, mark_class = "", ""
        if is_selected and is_correct:
            border, row_bg = "#2E7D32", "rgba(46,125,50,0.08)"
        elif is_selected and not is_correct:
            border, row_bg = "#C62828", "rgba(198,40,40,0.08)"
        else:
            border, row_bg = "#BBBBBB", "transparent"
        box = "☑" if is_selected else "☐"
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:10px;"
            f"border:1.5px solid {border};background:{row_bg};border-radius:6px;"
            f"padding:8px 12px;margin-bottom:6px'>"
            f"<span class='edir-mark {mark_class}'>{mark}</span>"
            f"<span style='font-size:1.2em;line-height:1'>{box}</span>"
            f"<span>{html.escape(option_text)}</span></div>",
            unsafe_allow_html=True,
        )


def _your_answer_heading(
    q_type: str, user_answer, correct_indices: set[int], total_options: int = 0
) -> str:
    """"Correct answers" heading: (correct picks / total correct) plus the
    official MRQ-formula score in parentheses, e.g. "Correct answers - 3/4 (0.75)".
    """
    if q_type == "free_text" or not correct_indices:
        return "**Your answer**"
    if isinstance(user_answer, int):
        selected = {user_answer}
    elif isinstance(user_answer, list):
        selected = set(user_answer)
    else:
        selected = set()
    hits = len(selected & correct_indices)
    score = mrq_score(selected, correct_indices, total_options)
    return f"**Correct answers - {hits}/{len(correct_indices)} ({score:.2f})**"


def _correct_indices_for(q_id: int, options: list[str]) -> set[int]:
    ans_row = get_answer(q_id)
    if not ans_row:
        return set()
    return set(
        correct_option_indices(options, ans_row["correct_options"], ans_row["answer_text"])
    )


def _render_correct_answer(
    question_id: int,
    options: list[str],
    *,
    show_details: bool = True,
    collapse_explanation: bool = False,
    question: dict | None = None,
    after_correct=None,
    show_correct_text: bool = True,
):
    ans_row = get_answer(question_id)
    if show_correct_text:
        if ans_row and ans_row["answer_text"]:
            st.markdown(ans_row["answer_text"])
        elif ans_row and options:
            indices = correct_option_indices(
                options, ans_row["correct_options"], ans_row["answer_text"]
            )
            if indices:
                for index in indices:
                    st.markdown(f"→ {options[index]}")
            else:
                st.markdown("_Answer not available_")
        else:
            st.markdown("_Answer not available_")

    if after_correct is not None:
        after_correct()

    if not show_details:
        return
    if ans_row and ans_row["explanation"]:
        if collapse_explanation:
            with st.expander("Explanation", expanded=False):
                st.markdown(ans_row["explanation"])
        else:
            st.markdown("**Explanation**")
            st.markdown(ans_row["explanation"])
    if question:
        _render_source_citation(question)
    answer_imgs = _load_images(ans_row["page_images"] if ans_row else None)
    if answer_imgs:
        st.markdown("**Answer images**")
        _show_images(answer_imgs, small=True, grid_cols=2)
    if question:
        _render_original_answer_page(question)


def _custom_answer_input(test_id: int, q: dict, *, disabled: bool):
    saved = q["user_answer_value"]
    options = json.loads(q.get("options") or "[]")
    key = f"custom_answer_{test_id}_{q['position']}"
    if disabled:
        # Already graded — the feedback view below shows the answer instead
        # of duplicating it here.
        return saved, options
    if q["q_type"] == "free_text":
        value = st.text_area(
            "Your answer",
            value=saved or "",
            height=160,
            key=key,
        )
    elif q["q_type"] == "single_choice":
        index = saved if isinstance(saved, int) and saved < len(options) else None
        choice = st.radio(
            "Select one:",
            options,
            index=index,
            key=key,
        )
        value = options.index(choice) if choice in options else None
    else:
        prev_sel = saved if isinstance(saved, list) else []
        st.caption("Select all that apply:")
        value = _render_mc_checkbox_input(
            options, prev_sel, key_prefix=key, disabled=False,
        )

    if value != saved and (
        _has_user_answer(q["q_type"], value) or saved is not None
    ):
        save_custom_progress(test_id, q["position"], value)
    return value, options


_CUSTOM_RESULT_LABELS = {
    "correct": "Correct",
    "partial": "Partially correct",
    "incorrect": "Incorrect",
    "skipped": "Skipped",
    "unrated": "Needs self-rating",
    None: "Not completed",
}


def _show_custom_feedback(q: dict, options: list[str]):
    result = q["result"]
    feedback = {
        "correct": (st.success, "Correct"),
        "partial": (st.warning, "Partially correct"),
        "incorrect": (st.error, "Incorrect"),
        "skipped": (st.info, "Skipped"),
        "unrated": (st.warning, "Compare your answer, then rate yourself"),
    }
    message_fn, label = feedback[result]
    message_fn(label)

    correct_indices = _correct_indices_for(q["question_id"], options)
    st.markdown(
        _your_answer_heading(q["q_type"], q["user_answer_value"], correct_indices, len(options))
    )
    if q["q_type"] == "free_text":
        _render_free_text_answer(q["user_answer_value"])
        st.markdown("**Correct answer**")
    else:
        _render_choice_feedback_grid(options, q["user_answer_value"], correct_indices)

    _render_correct_answer(
        q["question_id"], options, collapse_explanation=True, question=q,
        show_correct_text=(q["q_type"] == "free_text"),
    )


def _render_custom_section_builder(section: str, availability: list[dict]) -> list[dict]:
    label = SECTION_LABELS[section]
    key_prefix = f"{_library_key()}_{section}"
    rows = [row for row in availability if row["section"] == section]
    chapter_map = {}
    for row in rows:
        chapter_map[row["chapter_id"]] = (
            row["chapter_number"],
            row["chapter_title"],
        )

    with st.expander(f"{label} availability", expanded=False):
        if section == "mrq":
            table = [
                {
                    "Chapter": f"{row['chapter_number']}. {row['chapter_title']}",
                    "Source": row["source"],
                    "MRQ questions": row["question_count"],
                }
                for row in rows
            ]
        else:
            table = [
                {
                    "Chapter": f"{row['chapter_number']}. {row['chapter_title']}",
                    "Source": row["source"],
                    "Cases": row["case_count"],
                    "Questions": row["question_count"],
                }
                for row in rows
            ]
        st.dataframe(table, use_container_width=True, hide_index=True)

    selected_chapters = st.multiselect(
        f"{label} chapters",
        sorted(chapter_map, key=lambda cid: chapter_map[cid][0]),
        format_func=lambda cid: f"{chapter_map[cid][0]}. {chapter_map[cid][1]}",
        key=f"custom_chapters_{key_prefix}",
    )
    entries = []
    unit_label = "MRQ questions" if section == "mrq" else "cases"
    for chapter_id in selected_chapters:
        chapter_number, chapter_title = chapter_map[chapter_id]
        with st.container(border=True):
            st.markdown(f"**Chapter {chapter_number}: {chapter_title}**")
            chapter_rows = [row for row in rows if row["chapter_id"] == chapter_id]
            source_counts = {row["source"]: row["unit_count"] for row in chapter_rows}
            sources = st.multiselect(
                "Sources",
                sorted(source_counts),
                format_func=lambda source: f"{source} ({source_counts[source]})",
                key=f"custom_sources_{key_prefix}_{chapter_id}",
            )
            if not sources:
                st.caption("Select at least one source.")
                continue
            available_count = sum(source_counts[source] for source in sources)
            count_key = f"custom_count_{key_prefix}_{chapter_id}"
            if st.session_state.get(count_key, 1) > available_count:
                st.session_state[count_key] = available_count
            count = st.number_input(
                f"Number of {unit_label}",
                min_value=1,
                max_value=max(1, available_count),
                value=min(1, available_count),
                step=1,
                key=count_key,
            )
            st.caption(f"{available_count} eligible {unit_label} in the combined pool")
            entries.append(
                {
                    "chapter_id": chapter_id,
                    "sources": sources,
                    "count": int(count),
                }
            )
    return entries


def _custom_config_summary(config: dict) -> str:
    if is_phased_config(config):
        parts = []
        for phase in config.get("phases", []):
            count = sum(entry["count"] for entry in phase.get("entries", []))
            unit = "questions" if phase["section"] == "mrq" else "cases"
            parts.append(f"{count} {SECTION_LABELS[phase['section']]} {unit}")
        return " · ".join(parts) if parts else "Empty phased configuration"
    parts = []
    for section in ("core", "sc", "mrq"):
        count = sum(entry["count"] for entry in config["sections"].get(section, []))
        if count:
            unit = "questions" if section == "mrq" else "cases"
            parts.append(f"{count} {SECTION_LABELS[section]} {unit}")
    return " · ".join(parts) if parts else "Empty configuration"


def _custom_ordering_summary(config: dict) -> str:
    if is_phased_config(config):
        return "Fixed phases: MRQ → SC → CORE"
    ordering = get_custom_ordering(config)
    if ordering["mode"] == "mixed":
        return "Mixed throughout the test"
    active_sections = [
        section
        for section in ordering["section_order"]
        if config.get("sections", {}).get(section)
    ]
    labels = [SECTION_LABELS[section] for section in active_sections]
    return "Sequential: " + (" → ".join(labels) if labels else "no content selected")


def _open_custom_test(test_id: int):
    start_custom_test(test_id)
    st.session_state.custom_test_id = test_id
    st.session_state.custom_view = "test"


def _test_matches_library(test: dict) -> bool:
    return (test.get("config") or {}).get("library", LIBRARY_EDIR) == _library_key()


def _render_custom_builder():
    st.subheader("Build a new custom test")
    mode = st.radio(
        "Mode",
        ["exam", "learning"],
        format_func=lambda value: "Exam mode" if value == "exam" else "Learning mode",
        horizontal=True,
        key="custom_builder_mode",
    )
    if mode == "exam":
        timer_minutes = st.number_input(
            "Total time limit (minutes)",
            min_value=1,
            max_value=600,
            value=60,
            step=5,
            key="custom_builder_timer",
        )
        timer_limit_s = int(timer_minutes * 60)
    else:
        st.info("Learning mode is untimed.")
        timer_limit_s = None

    test_name = st.text_input(
        "Test name (optional)",
        placeholder="A date-based name will be generated automatically",
        key="custom_builder_test_name",
    )
    exclude_used = st.checkbox(
        "Exclude items already used in other custom tests (In Progress or History)",
        key="custom_builder_exclude_used",
    )
    if _library_key() != LIBRARY_UEFA_CFM:
        selected_modalities = st.multiselect(
            "Imaging modality (CORE & SC only)",
            MODALITIES,
            default=MODALITIES,
            key="custom_builder_modalities",
        )
        if selected_modalities and set(selected_modalities) != set(MODALITIES):
            st.caption(
                "MRQs are unaffected — CORE/SC cases are filtered to those "
                "showing at least one selected modality."
            )
    else:
        selected_modalities = MODALITIES
    st.markdown("#### Content ordering")
    if _library_key() == LIBRARY_UEFA_CFM:
        ordering_mode = "sequential"
        section_order = ["mrq"]
        st.info(
            "UEFA CFM custom tests draw individual MRQs from the handbook "
            "chapters selected below."
        )
    else:
        ordering_mode = st.radio(
            "How should content types be presented?",
            ["sequential", "mixed"],
            format_func=lambda value: (
                "Sequential — keep each content type together"
                if value == "sequential"
                else "Mixed — interleave all selected content types"
            ),
            horizontal=True,
            key="custom_builder_ordering_mode",
        )
        if ordering_mode == "sequential":
            st.caption(
                "Choose the section order. Content types with no selected questions are skipped."
            )
            order_cols = st.columns(3)
            section_order = []
            for index, (column, label) in enumerate(
                zip(order_cols, ("First", "Second", "Third"))
            ):
                with column:
                    section_order.append(
                        st.selectbox(
                            label,
                            list(SECTION_ORDER),
                            index=index,
                            format_func=lambda section: SECTION_LABELS[section],
                            key=f"custom_builder_section_order_{index}",
                        )
                    )
        else:
            section_order = list(SECTION_ORDER)
            st.info(
                "CORE and Short Cases will be spread among the other content. "
                "Each case stays intact and its internal questions remain consecutive."
            )
    ordering = {
        "mode": ordering_mode,
        "section_order": section_order,
    }

    availability = get_custom_availability(
        library_key=_library_key(),
        modalities=selected_modalities,
        exclude_used=exclude_used,
    )
    entries = {}
    if _library_key() == LIBRARY_UEFA_CFM:
        entries["mrq"] = _render_custom_section_builder("mrq", availability)
    else:
        section_tabs = st.tabs(["CORE", "SC", "MRQ"])
        for tab, section in zip(section_tabs, ("core", "sc", "mrq")):
            with tab:
                entries[section] = _render_custom_section_builder(
                    section, availability
                )
    config = {
        "version": CONFIG_VERSION,
        "library": _library_key(),
        "ordering": ordering,
        "sections": entries,
        "modalities": selected_modalities,
        "exclude_used": exclude_used,
    }

    st.markdown("---")
    st.markdown(f"**Selection:** {_custom_config_summary(config)}")
    st.caption(_custom_ordering_summary(config))
    filter_notes = []
    if exclude_used:
        filter_notes.append("excluding items already used in other custom tests")
    if set(selected_modalities) != set(MODALITIES):
        modality_list = ", ".join(selected_modalities) if selected_modalities else "none"
        filter_notes.append(f"CORE/SC modality filter: {modality_list}")
    if filter_notes:
        st.caption("Active filters: " + "; ".join(filter_notes))
    errors = validate_custom_config(config)
    for error in errors:
        st.warning(error)

    template_name = st.text_input(
        "Template name",
        placeholder="Required only when saving this configuration",
        key="custom_builder_template_name",
    )
    action_cols = st.columns(2)
    with action_cols[0]:
        if st.button(
            "Save as template",
            use_container_width=True,
            disabled=bool(errors) or not template_name.strip(),
            key="custom_save_template",
        ):
            save_custom_template(
                template_name.strip(), mode, timer_limit_s, config
            )
            st.success("Template saved.")
    with action_cols[1]:
        if st.button(
            "Generate and start",
            type="primary",
            use_container_width=True,
            disabled=bool(errors),
            key="custom_generate",
        ):
            name = test_name.strip() or _custom_default_name()
            try:
                test_id = create_custom_test(name, mode, timer_limit_s, config)
            except ValueError as exc:
                st.error(str(exc))
            else:
                _open_custom_test(test_id)
                st.rerun()


def _render_phased_template_editor():
    editor = st.session_state.custom_phase_editor
    config = editor["config"]
    nonce = st.session_state.custom_phase_editor_nonce

    st.markdown("---")
    st.subheader("Customize phased exam")
    st.info(
        "This copy remains Exam-only and keeps the MRQ → SC → CORE order. "
        "Set a chapter quota to zero to omit it."
    )
    name = st.text_input(
        "Template name",
        value=editor["name"],
        key=f"phased_editor_name_{nonce}",
    )
    exclude_used = st.checkbox(
        "Exclude items already used in other custom tests (In Progress or History)",
        value=bool(config.get("exclude_used")),
        key=f"phased_editor_exclude_used_{nonce}",
    )
    availability = get_custom_availability(
        library_key=LIBRARY_EDIR, exclude_used=exclude_used
    )
    edited_phases = []
    for phase in config["phases"]:
        section = phase["section"]
        section_rows = [row for row in availability if row["section"] == section]
        rows_by_chapter = {}
        for row in section_rows:
            rows_by_chapter.setdefault(row["chapter_id"], []).append(row)
        saved_entries = {
            int(entry["chapter_id"]): entry for entry in phase.get("entries", [])
        }
        with st.expander(
            f"{phase['phase_index'] + 1}. {phase['name']}", expanded=True
        ):
            timer_minutes = st.number_input(
                "Timer (minutes)",
                min_value=1,
                max_value=600,
                value=max(1, int(phase["timer_limit_s"] // 60)),
                step=5,
                key=f"phased_timer_{nonce}_{section}",
            )
            edited_entries = []
            for chapter_id in sorted(
                rows_by_chapter,
                key=lambda value: rows_by_chapter[value][0]["chapter_number"],
            ):
                first = rows_by_chapter[chapter_id][0]
                source_counts = {
                    row["source"]: int(row["unit_count"])
                    for row in rows_by_chapter[chapter_id]
                }
                all_sources = sorted(source_counts)
                saved = saved_entries.get(chapter_id, {})
                saved_sources = saved.get("sources", "*")
                defaults = (
                    all_sources
                    if saved_sources == "*"
                    else [source for source in saved_sources if source in source_counts]
                )
                st.markdown(
                    f"**{first['chapter_number']}. {first['chapter_title']}**"
                )
                source_col, quota_col = st.columns([3, 1])
                with source_col:
                    sources = st.multiselect(
                        "Sources",
                        all_sources,
                        default=defaults,
                        format_func=lambda source, counts=source_counts: (
                            f"{source} ({counts[source]})"
                        ),
                        key=f"phased_sources_{nonce}_{section}_{chapter_id}",
                        label_visibility="collapsed",
                    )
                available = sum(source_counts[source] for source in sources)
                default_count = min(int(saved.get("count", 0)), available)
                with quota_col:
                    count = st.number_input(
                        "Quota",
                        min_value=0,
                        max_value=max(0, available),
                        value=default_count,
                        step=1,
                        key=f"phased_count_{nonce}_{section}_{chapter_id}",
                        label_visibility="collapsed",
                    )
                st.caption(
                    f"{available} available "
                    f"{'questions' if section == 'mrq' else 'cases'}"
                )
                if count:
                    edited_entries.append(
                        {
                            "chapter_id": chapter_id,
                            "sources": sources,
                            "count": int(count),
                        }
                    )
            edited_phases.append(
                {
                    "phase_index": phase["phase_index"],
                    "section": section,
                    "name": phase["name"],
                    "timer_limit_s": int(timer_minutes * 60),
                    "entries": edited_entries,
                }
            )

    edited_config = {
        "version": CONFIG_VERSION,
        "library": LIBRARY_EDIR,
        "structure": "phased_exam",
        "phases": edited_phases,
        "exclude_used": exclude_used,
    }
    st.markdown(f"**Selection:** {_custom_config_summary(edited_config)}")
    errors = validate_custom_config(edited_config)
    for error in errors:
        st.warning(error)
    save_col, cancel_col = st.columns(2)
    with save_col:
        label = "Save changes" if editor["template_id"] else "Save as new template"
        if st.button(
            label,
            type="primary",
            use_container_width=True,
            disabled=bool(errors) or not name.strip(),
            key=f"phased_editor_save_{nonce}",
        ):
            if editor["template_id"]:
                update_custom_template(
                    editor["template_id"], name.strip(), "exam", None, edited_config
                )
            else:
                save_custom_template(name.strip(), "exam", None, edited_config)
            st.session_state.custom_phase_editor = None
            st.success("Phased template saved.")
            st.rerun()
    with cancel_col:
        if st.button(
            "Cancel",
            use_container_width=True,
            key=f"phased_editor_cancel_{nonce}",
        ):
            st.session_state.custom_phase_editor = None
            st.rerun()


def _render_custom_templates():
    if _library_key() == LIBRARY_EDIR:
        official = get_official_edir_config()
        st.subheader("Official preset")
        with st.container(border=True):
            st.markdown("### Official EDiR Exam")
            st.caption(
                "Exam only · 78 MRQs (95 min) → break → "
                "24 Short Cases (90 min) → break → 10 CORE cases (90 min)"
            )
            st.caption(
                "Uses all currently available sources and follows the official chapter blueprint."
            )
            official_exclude_used = st.checkbox(
                "Exclude items already used in other custom tests (In Progress or History)",
                key="official_edir_exclude_used",
            )
            official_actions = st.columns(2)
            with official_actions[0]:
                if st.button(
                    "Generate Exam",
                    type="primary",
                    use_container_width=True,
                    key="official_edir_generate",
                ):
                    official_config = {**official, "exclude_used": official_exclude_used}
                    try:
                        test_id = create_custom_test(
                            _custom_default_name("Official EDiR Exam"),
                            "exam",
                            None,
                            official_config,
                        )
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        _open_custom_test(test_id)
                        st.rerun()
            with official_actions[1]:
                if st.button(
                    "Customize",
                    use_container_width=True,
                    key="official_edir_customize",
                ):
                    st.session_state.custom_phase_editor_nonce += 1
                    st.session_state.custom_phase_editor = {
                        "template_id": None,
                        "name": "Official EDiR Exam — Custom",
                        "config": {**official, "exclude_used": official_exclude_used},
                    }
                    st.rerun()

    if st.session_state.custom_phase_editor:
        _render_phased_template_editor()
        return

    templates = get_custom_templates(_library_key())
    st.subheader("Saved templates")
    if not templates:
        st.info("No saved templates yet.")
        return
    for template in templates:
        with st.container(border=True):
            phased = is_phased_config(template["config"])
            info, action = st.columns([4, 1.4])
            with info:
                st.markdown(f"**{template['name']}**")
                if phased:
                    st.caption(
                        f"Phased exam · {_custom_config_summary(template['config'])}"
                    )
                    st.caption(
                        "MRQ / SC / CORE timers: "
                        + " / ".join(
                            f"{phase['timer_limit_s'] // 60} min"
                            for phase in template["config"]["phases"]
                        )
                    )
                else:
                    st.caption(
                        f"{'Exam' if template['mode'] == 'exam' else 'Learning'} · "
                        f"{_custom_config_summary(template['config'])}"
                    )
                    st.caption(_custom_ordering_summary(template["config"]))
                if template["mode"] == "exam" and not phased:
                    st.caption(f"{template['timer_limit_s'] // 60} minute timer")
            with action:
                if st.button(
                    "Generate",
                    type="primary",
                    use_container_width=True,
                    key=f"custom_template_generate_{template['id']}",
                ):
                    name = _custom_default_name(template["name"])
                    try:
                        test_id = create_custom_test(
                            name,
                            template["mode"],
                            template["timer_limit_s"],
                            template["config"],
                            template_id=template["id"],
                        )
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        _open_custom_test(test_id)
                        st.rerun()
                if phased and st.button(
                    "Edit",
                    use_container_width=True,
                    key=f"custom_template_edit_{template['id']}",
                ):
                    st.session_state.custom_phase_editor_nonce += 1
                    st.session_state.custom_phase_editor = {
                        "template_id": template["id"],
                        "name": template["name"],
                        "config": template["config"],
                    }
                    st.rerun()
                if st.button(
                    "Delete",
                    use_container_width=True,
                    key=f"custom_template_delete_{template['id']}",
                ):
                    st.session_state.custom_delete_template_id = template["id"]
            if st.session_state.custom_delete_template_id == template["id"]:
                st.warning(
                    f"Delete the template “{template['name']}”? "
                    "Tests generated from it will be kept."
                )
                confirm, cancel = st.columns(2)
                with confirm:
                    if st.button(
                        "Confirm template deletion",
                        type="primary",
                        use_container_width=True,
                        key=f"custom_template_confirm_delete_{template['id']}",
                    ):
                        delete_custom_template(template["id"])
                        st.session_state.custom_delete_template_id = None
                        st.rerun()
                with cancel:
                    if st.button(
                        "Cancel",
                        use_container_width=True,
                        key=f"custom_template_cancel_delete_{template['id']}",
                    ):
                        st.session_state.custom_delete_template_id = None
                        st.rerun()


def _render_custom_test_list(statuses: tuple[str, ...], *, history: bool = False):
    tests = get_custom_tests(statuses, library_key=_library_key())
    if not tests:
        st.info("No completed custom tests yet." if history else "No tests to resume.")
        return
    for test in tests:
        with st.container(border=True):
            info, action = st.columns([4, 1])
            with info:
                st.markdown(f"**{test['name']}**")
                created = datetime.datetime.fromtimestamp(test["created_at"]).strftime(
                    "%d %b %Y %H:%M"
                )
                st.caption(
                    f"{'Exam' if test['mode'] == 'exam' else 'Learning'} · "
                    f"{test['question_count']} questions · {created}"
                )
                if test.get("structure") == "phased_exam":
                    phases = get_custom_test_phases(test["id"])
                    current_index = int(test.get("current_phase") or 0)
                    current = next(
                        (
                            phase
                            for phase in phases
                            if phase["phase_index"] == current_index
                        ),
                        None,
                    )
                    if current:
                        if (
                            current["status"] == "completed"
                            and current_index + 1 < len(phases)
                        ):
                            next_phase = phases[current_index + 1]
                            st.info(f"Break before {next_phase['name']}")
                        elif test["status"] != "completed":
                            st.info(
                                f"Phase {current_index + 1} of {len(phases)}: "
                                f"{current['name']}"
                            )
                if not history:
                    completed = test["completed_count"] or 0
                    st.progress(
                        completed / max(test["question_count"], 1),
                        text=f"{completed}/{test['question_count']} completed",
                    )
            with action:
                label = "Review" if history else (
                    "Start" if test["status"] == "ready" else "Resume"
                )
                if st.button(
                    label,
                    type="primary",
                    use_container_width=True,
                    key=f"custom_open_{test['id']}_{label}",
                ):
                    st.session_state.custom_test_id = test["id"]
                    if history:
                        st.session_state.custom_view = (
                            "summary" if test["mode"] == "learning" else "review"
                        )
                    else:
                        _open_custom_test(test["id"])
                    st.rerun()
                if st.button(
                    "Delete",
                    use_container_width=True,
                    key=f"custom_test_delete_{test['id']}",
                ):
                    st.session_state.custom_delete_test_id = test["id"]
            if st.session_state.custom_delete_test_id == test["id"]:
                location = "history" if history else "in-progress tests"
                st.warning(
                    f"Permanently delete “{test['name']}” from {location}? "
                    "Its saved answers and progress will also be deleted."
                )
                confirm, cancel = st.columns(2)
                with confirm:
                    if st.button(
                        "Confirm test deletion",
                        type="primary",
                        use_container_width=True,
                        key=f"custom_test_confirm_delete_{test['id']}",
                    ):
                        deleted = delete_custom_test(test["id"])
                        if deleted and st.session_state.custom_test_id == test["id"]:
                            st.session_state.custom_test_id = None
                            st.session_state.custom_view = "dashboard"
                        st.session_state.custom_delete_test_id = None
                        st.rerun()
                with cancel:
                    if st.button(
                        "Cancel",
                        use_container_width=True,
                        key=f"custom_test_cancel_delete_{test['id']}",
                    ):
                        st.session_state.custom_delete_test_id = None
                        st.rerun()


def view_custom_dashboard():
    st.header(f"{_library_label()} custom tests")
    build_tab, templates_tab, progress_tab, history_tab = st.tabs(
        ["Build New", "Templates", "In Progress", "History"]
    )
    with build_tab:
        _render_custom_builder()
    with templates_tab:
        _render_custom_templates()
    with progress_tab:
        _render_custom_test_list(("ready", "in_progress"))
    with history_tab:
        _render_custom_test_list(("completed",), history=True)


def _grade_custom_learning_answer(q: dict, user_answer, options: list[str]) -> str:
    if q["q_type"] == "free_text":
        return "unrated"
    ans_row = get_answer(q["question_id"])
    return classify_answer(
        q_type=q["q_type"],
        user_answer=user_answer,
        options=options,
        correct_options=ans_row["correct_options"] if ans_row else None,
        answer_text=ans_row["answer_text"] if ans_row else None,
    )


def _render_custom_media(q: dict):
    imgs = _load_images(q.get("page_images"))
    if imgs:
        _show_images(
            imgs,
            captions=_load_image_captions(q.get("page_image_captions")),
            grid_cols=2,
        )
    for index, url in enumerate(json.loads(q.get("video_links") or "[]"), 1):
        st.markdown(f"[▶ Video {index}]({url})")


def _render_custom_article_summary(q: dict) -> None:
    """Show a question's saved source-article summary after feedback is revealed."""
    article_summary = (q.get("article_summary") or "").strip()
    if article_summary:
        with st.expander("Article summary", expanded=False):
            st.markdown(article_summary)


def _phase_content_label(phase: dict, questions: list[dict]) -> str:
    if phase["section"] == "mrq":
        return f"{len(questions)} MRQ questions"
    cases = len({q["case_id"] for q in questions})
    return f"{cases} {SECTION_LABELS[phase['section']]} cases"


def _section_case_progress(questions: list[dict], current_q: dict) -> str | None:
    """For a CORE/SC question, return e.g. "SC case 2 of 24" — the current
    case's rank among same-section cases in this question list. MRQ returns
    None since "Question X of Y" already conveys the same thing there (each
    MRQ is its own unit).
    """
    section = current_q["section"]
    if section not in ("core", "sc"):
        return None
    unit_positions = []
    for q in questions:
        if q["section"] == section and q["unit_position"] not in unit_positions:
            unit_positions.append(q["unit_position"])
    case_number = unit_positions.index(current_q["unit_position"]) + 1
    return f"{SECTION_LABELS[section]} case {case_number} of {len(unit_positions)}"


def _render_phased_custom_test(test: dict):
    test_id = test["id"]
    phases = get_custom_test_phases(test_id)
    phase_index = int(test["current_phase"])
    if phase_index >= len(phases):
        st.error("The current exam phase is invalid.")
        return
    phase = phases[phase_index]

    if st.button("← Custom dashboard", key="phased_back_dashboard"):
        st.session_state.custom_view = "dashboard"
        st.rerun()
    st.header(test["name"])

    if phase["status"] == "completed" and phase_index < len(phases) - 1:
        next_phase = phases[phase_index + 1]
        next_questions = get_custom_test_questions(test_id, phase_index + 1)
        st.success(f"{phase['name']} completed")
        st.subheader("Break")
        st.info(
            "This break is untimed. Your completed section is locked, and answers "
            "remain hidden until the entire exam is complete."
        )
        actual = phase.get("time_taken_s")
        if actual is not None:
            st.caption(f"Section time: {_fmt_time(actual)}")
        st.markdown(
            f"**Next:** {next_phase['name']} · "
            f"{_phase_content_label(next_phase, next_questions)} · "
            f"{next_phase['timer_limit_s'] // 60} minutes"
        )
        if st.button(
            f"Continue to {next_phase['name']}",
            type="primary",
            use_container_width=True,
            key=f"continue_phase_{test_id}_{phase_index + 1}",
        ):
            if continue_custom_phase(test_id):
                st.rerun()
            else:
                st.error("The next phase could not be started. Please reload and try again.")
        return

    questions = get_custom_test_questions(test_id, phase_index)
    if not questions:
        st.error("This phase has no questions.")
        return
    if phase["status"] == "ready":
        start_custom_test(test_id)
        phase = get_custom_test_phases(test_id)[phase_index]

    phase = get_custom_test_phases(test_id)[phase_index]
    phase_paused_at = phase.get("paused_at")
    phase_started_at = phase["started_at"] or time.time()
    phase_elapsed = (phase_paused_at or time.time()) - phase_started_at
    phase_remaining = max(0.0, phase["timer_limit_s"] - phase_elapsed)
    with st.sidebar:
        _render_js_countdown(
            _timer_slot, phase_remaining,
            label=f"PHASE {phase_index + 1} TIME",
            ticking=not phase_paused_at,
        )
    # Isolated fragment that only watches for time-up; kept out of the
    # sidebar (a @st.fragment cannot write to the sidebar in this version).
    _watch_phase_timer_expiry(test_id, phase_index, phase_index == len(phases) - 1)
    _render_phase_pause_button(test_id, phase_index, phase_paused_at)
    if phase_paused_at:
        st.info(
            "Phase paused — the countdown is frozen and your progress is saved. "
            "Press **Resume timer** in the sidebar to continue."
        )
        return

    positions = [q["position"] for q in questions]
    current_global = int(test["current_position"])
    local_index = positions.index(current_global) if current_global in positions else 0
    q = questions[local_index]
    st.markdown(
        f"**Phase {phase_index + 1} of {len(phases)} — {phase['name']}**"
    )
    st.progress(
        (local_index + 1) / len(questions),
        text=f"Question {local_index + 1} of {len(questions)} in this phase",
    )
    case_progress = _section_case_progress(questions, q)
    if case_progress:
        st.caption(case_progress)
    col_q, col_img = st.columns([1, 1], gap="large")
    with col_q:
        # Source is intentionally hidden here — phased exams are exam-mode
        # only, and seeing the source book can hint at the answer.
        st.markdown(f"### {SECTION_LABELS[q['section']]} Q{q['q_number']}")
        if q["section"] in ("core", "sc") and q.get("clinical_vignette"):
            st.info(q["clinical_vignette"])
        st.markdown(q["question_text"])
        _custom_answer_input(test_id, q, disabled=False)
        st.markdown("---")
        nav = st.columns([1, 1, 2])
        with nav[0]:
            if local_index > 0 and st.button(
                "← Previous",
                use_container_width=True,
                key=f"phased_prev_{phase_index}",
            ):
                set_custom_position(test_id, positions[local_index - 1])
                st.rerun()
        with nav[2]:
            if local_index < len(questions) - 1:
                if st.button(
                    "Next →",
                    type="primary",
                    use_container_width=True,
                    key=f"phased_next_{phase_index}",
                ):
                    set_custom_position(test_id, positions[local_index + 1])
                    st.rerun()
            elif st.button(
                f"Complete {phase['name']}",
                type="primary",
                use_container_width=True,
                key=f"phased_complete_{phase_index}",
            ):
                finish_custom_phase(test_id, phase_index)
                if phase_index == len(phases) - 1:
                    st.session_state.custom_view = "review"
                st.rerun()
    with col_img:
        _render_custom_media(q)


def view_custom_test():
    test_id = st.session_state.custom_test_id
    test = get_custom_test(test_id) if test_id else None
    if not test:
        st.error("Custom test not found.")
        st.session_state.custom_view = "dashboard"
        return
    if not _test_matches_library(test):
        st.error("This custom test belongs to a different library.")
        st.session_state.custom_test_id = None
        st.session_state.custom_view = "dashboard"
        return
    if test["status"] == "completed":
        st.session_state.custom_view = (
            "summary" if test["mode"] == "learning" else "review"
        )
        st.rerun()

    if test["status"] == "ready":
        start_custom_test(test_id)
        test = get_custom_test(test_id)
    if test.get("structure") == "phased_exam":
        _render_phased_custom_test(test)
        return
    questions = get_custom_test_questions(test_id)
    if not questions:
        st.error("This custom test has no questions.")
        return
    position = min(test["current_position"], len(questions) - 1)
    q = questions[position]
    is_learning = test["mode"] == "learning"

    if not is_learning:
        test_paused_at = test.get("paused_at")
        test_remaining = max(
            0.0, test["timer_limit_s"] - ((test_paused_at or time.time()) - test["started_at"])
        )
        with st.sidebar:
            _render_js_countdown(
                _timer_slot, test_remaining,
                label="TIME REMAINING", ticking=not test_paused_at,
            )
        # Isolated fragment that only watches for time-up; kept out of the
        # sidebar (a @st.fragment cannot write to the sidebar in this version).
        _watch_custom_test_timer_expiry(test_id)
        _render_custom_test_pause_button(test_id, test_paused_at)
        if test_paused_at:
            st.info(
                "Test paused — the countdown is frozen and your progress is saved. "
                "Press **Resume timer** in the sidebar to continue."
            )
            return

    if st.button("← Custom dashboard"):
        st.session_state.custom_view = "dashboard"
        st.rerun()
    st.header(test["name"])
    st.progress(
        (position + 1) / len(questions),
        text=f"Question {position + 1} of {len(questions)}",
    )
    case_progress = _section_case_progress(questions, q)
    if case_progress:
        st.caption(case_progress)
    col_q, col_img = st.columns([1, 1], gap="large")
    with col_q:
        if is_learning:
            # Hidden in exam mode — seeing the source book can hint at the answer.
            st.caption(_custom_context_label(q))
        st.markdown(f"### {SECTION_LABELS[q['section']]} Q{q['q_number']}")
        if q["section"] in ("core", "sc") and q.get("clinical_vignette"):
            st.info(q["clinical_vignette"])
        st.markdown(q["question_text"])
        revealed = bool(q["revealed"])
        user_answer, options = _custom_answer_input(
            test_id, q, disabled=is_learning and revealed
        )

        if is_learning and revealed:
            _show_custom_feedback(q, options)
            _render_custom_article_summary(q)
            if q["result"] == "unrated":
                st.markdown(
                    "**Self-rating** — this score feeds into this case's and this "
                    "section's overall percentage once saved."
                )
                self_score = st.slider(
                    "0 = fully missed · 1 = fully correct",
                    min_value=0.0, max_value=1.0, value=0.5, step=0.05,
                    key=f"custom_selfscore_{test_id}_{position}",
                )
                if st.button(
                    "Save rating",
                    key=f"custom_saverating_{test_id}_{position}",
                ):
                    rate_custom_free_text(test_id, position, self_score)
                    st.rerun()

                st.text_area(
                    "Scratch notes (not saved)",
                    key=f"custom_scratch_{test_id}_{position}",
                    height=120,
                    placeholder="Jot down anything you like — this is just for practice and is never saved.",
                )

        st.markdown("---")
        if is_learning:
            complete = q["result"] not in (None, "unrated")
            if not revealed:
                nav = st.columns([1, 2, 1])
                with nav[0]:
                    if position > 0 and st.button(
                        "← Previous", use_container_width=True, key="custom_learning_prev"
                    ):
                        set_custom_position(test_id, position - 1)
                        st.rerun()
                with nav[1]:
                    if st.button(
                        "Check answer",
                        type="primary",
                        use_container_width=True,
                        disabled=not _has_user_answer(q["q_type"], user_answer),
                        key="custom_learning_check",
                    ):
                        result = _grade_custom_learning_answer(q, user_answer, options)
                        save_custom_progress(
                            test_id,
                            position,
                            user_answer,
                            revealed=True,
                            result=result,
                        )
                        st.rerun()
                with nav[2]:
                    if st.button(
                        "Skip / Show answer",
                        use_container_width=True,
                        key="custom_learning_skip",
                    ):
                        save_custom_progress(
                            test_id,
                            position,
                            user_answer,
                            revealed=True,
                            result="skipped",
                        )
                        st.rerun()
            elif complete:
                nav = st.columns([1, 1, 2])
                with nav[0]:
                    if position > 0 and st.button(
                        "← Previous", use_container_width=True, key="custom_done_prev"
                    ):
                        set_custom_position(test_id, position - 1)
                        st.rerun()
                with nav[2]:
                    if position < len(questions) - 1:
                        if st.button(
                            "Next question →",
                            type="primary",
                            use_container_width=True,
                            key="custom_learning_next",
                        ):
                            set_custom_position(test_id, position + 1)
                            st.rerun()
                    elif st.button(
                        "Finish test",
                        type="primary",
                        use_container_width=True,
                        key="custom_learning_finish",
                    ):
                        finish_custom_test(test_id)
                        st.session_state.custom_view = "summary"
                        st.rerun()
        else:
            nav = st.columns([1, 1, 2])
            with nav[0]:
                if position > 0 and st.button(
                    "← Previous", use_container_width=True, key="custom_exam_prev"
                ):
                    set_custom_position(test_id, position - 1)
                    st.rerun()
            with nav[2]:
                if position < len(questions) - 1:
                    if st.button(
                        "Next →",
                        type="primary",
                        use_container_width=True,
                        key="custom_exam_next",
                    ):
                        set_custom_position(test_id, position + 1)
                        st.rerun()
                elif st.button(
                    "Submit test",
                    type="primary",
                    use_container_width=True,
                    key="custom_exam_submit",
                ):
                    finish_custom_test(test_id)
                    st.session_state.custom_view = "review"
                    st.rerun()
    with col_img:
        _render_custom_media(q)


def _custom_result_summary(test: dict, questions: list[dict]):
    counts = {
        result: sum(1 for q in questions if q["result"] == result)
        for result in ("correct", "partial", "incorrect", "skipped", "unrated")
    }
    metric_cols = st.columns(4)
    metric_cols[0].metric("Correct", counts["correct"])
    metric_cols[1].metric("Partial", counts["partial"])
    metric_cols[2].metric("Incorrect", counts["incorrect"])
    metric_cols[3].metric("Skipped", counts["skipped"])
    if counts["unrated"]:
        st.warning(f"{counts['unrated']} free-text answer(s) still need self-rating.")

    phases = (
        get_custom_test_phases(test["id"])
        if test.get("structure") == "phased_exam"
        else []
    )
    phase_names = {phase["phase_index"]: phase["name"] for phase in phases}

    scores = get_custom_phase_scores(test["id"])
    if scores:
        st.subheader("Phase scores" if phases else "Section scores")
        st.caption(
            "MRQ and SC score every question equally (non-free-text plus any "
            "free-text question you've self-rated below), using the official "
            "partial-credit formula. Each CORE case is instead weighted out of "
            "10 points — its first free-text question is worth 3, each "
            "additional free-text question 2, and the rest is split evenly "
            "across its non-free-text questions."
        )
        score_cols = st.columns(len(scores))
        for col, score in zip(score_cols, scores):
            col.metric(
                score["name"],
                f"{score['score_pct']:.1f}%",
                help=f"{score['scored_count']} scored question(s)",
            )

    if phases:
        st.subheader("Phase timing")
        st.dataframe(
            [
                {
                    "Phase": phase["name"],
                    "Limit": _fmt_time(phase["timer_limit_s"]),
                    "Actual": (
                        _fmt_time(phase["time_taken_s"])
                        if phase["time_taken_s"] is not None
                        else "—"
                    ),
                }
                for phase in phases
            ],
            use_container_width=True,
            hide_index=True,
        )

    breakdown = get_custom_result_breakdown(test["id"])
    table = [
        {
            **(
                {"Phase": phase_names.get(row["phase_index"], "Phase")}
                if phases
                else {}
            ),
            "Type": SECTION_LABELS[row["section"]],
            "Source": row["source"],
            "Result": _CUSTOM_RESULT_LABELS[row["result"]],
            "Questions": row["count"],
        }
        for row in breakdown
    ]
    if table:
        st.dataframe(table, use_container_width=True, hide_index=True)


def _question_score(q: dict) -> float | None:
    """A question's 0-1 partial-credit score. A free-text question only
    scores once self-rated (its 0-1 self_score is used directly); an
    unrated free-text question returns None, same as an unscored one."""
    if q["q_type"] == "free_text":
        return q.get("self_score")
    options = json.loads(q.get("options") or "[]")
    correct_indices = _correct_indices_for(q["question_id"], options)
    user_answer = q["user_answer_value"]
    if isinstance(user_answer, int):
        selected = {user_answer}
    elif isinstance(user_answer, list):
        selected = set(user_answer)
    else:
        selected = set()
    return mrq_score(selected, correct_indices, len(options))


def _case_score_pct(case_questions: list[dict]) -> float | None:
    """Average partial-credit score across a case's scorable questions —
    every question weighted equally. Used for SC (and any non-CORE) cases.
    Returns None if the case has no scorable question yet."""
    scores = [s for s in (_question_score(q) for q in case_questions) if s is not None]
    if not scores:
        return None
    return sum(scores) / len(scores) * 100


def _core_case_score(case_questions: list[dict]) -> tuple[float, float]:
    """A CORE case's weighted score out of 10 points (see score_core_case):
    the first free-text question is worth 3 points, each additional
    free-text question 2 points, and the remaining points split evenly
    across the non-free-text questions — reallocating fully to whichever
    type exists if a case is all one type. Returns (earned_points,
    max_points_so_far); an unrated free-text question's points are excluded
    from both until it's self-rated."""
    entries = [
        {
            "q_number": q["q_number"],
            "is_free_text": q["q_type"] == "free_text",
            "score": _question_score(q),
        }
        for q in case_questions
    ]
    return score_core_case(entries)


def _render_custom_review_question(test_id: int, q: dict, *, label: str, expanded: bool) -> None:
    result_label = _CUSTOM_RESULT_LABELS[q["result"]]
    title = f"{label} — {result_label}"
    if q["result"] == "unrated":
        title = f"🟡 {title}"
    options = json.loads(q.get("options") or "[]")
    correct_indices = _correct_indices_for(q["question_id"], options)
    with st.expander(title, expanded=expanded):
        col_q, col_a = st.columns(2, gap="large")
        with col_q:
            st.markdown("**Question**")
            st.markdown(q["question_text"])
            st.markdown(
                _your_answer_heading(
                    q["q_type"], q["user_answer_value"], correct_indices, len(options)
                )
            )
            if q["q_type"] == "free_text":
                _render_free_text_answer(q["user_answer_value"])
            else:
                _render_choice_feedback_grid(
                    options, q["user_answer_value"], correct_indices
                )
        with col_a:
            if q["q_type"] == "free_text":
                st.markdown("**Correct answer**")
            _render_correct_answer(
                q["question_id"], options, question=q,
                show_correct_text=(q["q_type"] == "free_text"),
            )
        if q["q_type"] == "free_text" and q["result"] == "unrated":
            st.markdown("---")
            st.markdown("**Self-rating** — this score feeds into this case's and this "
                         "section's overall percentage once saved.")
            score = st.slider(
                "0 = fully missed · 1 = fully correct",
                min_value=0.0, max_value=1.0, value=0.5, step=0.05,
                key=f"custom_review_selfscore_{test_id}_{q['position']}",
            )
            if st.button(
                "Save rating",
                key=f"custom_review_saverating_{test_id}_{q['position']}",
            ):
                rate_custom_free_text(test_id, q["position"], score)
                st.rerun()


def view_custom_results(*, compact: bool):
    test_id = st.session_state.custom_test_id
    test = get_custom_test(test_id) if test_id else None
    if not test:
        st.error("Custom test not found.")
        return
    if not _test_matches_library(test):
        st.error("This custom test belongs to a different library.")
        st.session_state.custom_test_id = None
        st.session_state.custom_view = "dashboard"
        return
    if test.get("structure") == "phased_exam" and test["status"] != "completed":
        st.warning("Answers are available only after all three exam phases are complete.")
        st.session_state.custom_view = "test"
        st.rerun()
    questions = get_custom_test_questions(test_id)
    if st.button("← Custom dashboard"):
        st.session_state.custom_view = "dashboard"
        st.rerun()
    st.header(f"{test['name']} — {'Summary' if compact else 'Review'}")
    _custom_result_summary(test, questions)

    st.markdown("---")
    hide_correct = st.checkbox(
        "Hide correct answers (show only partial/incorrect/skipped/unrated)",
        key=f"hide_correct_{test_id}",
        help="Also speeds up this page a lot on long tests, since every "
             "expander's content is skipped entirely rather than just collapsed.",
    )
    sections_present = [s for s in ("mrq", "sc", "core") if any(q["section"] == s for q in questions)]
    if not sections_present:
        return
    tabs = st.tabs([SECTION_LABELS[s] for s in sections_present])
    for section, tab in zip(sections_present, tabs):
        with tab:
            section_questions = [q for q in questions if q["section"] == section]
            if section == "mrq":
                shown = 0
                for idx, q in enumerate(section_questions, start=1):
                    if hide_correct and q["result"] == "correct":
                        continue
                    shown += 1
                    _render_custom_review_question(
                        test_id, q, label=f"MRQ {idx}",
                        expanded=compact and q["result"] in ("incorrect", "partial"),
                    )
                if shown == 0:
                    st.info("No partial, incorrect, skipped, or unrated MRQs.")
                continue
            cases: dict[int, list[dict]] = {}
            for q in section_questions:
                cases.setdefault(q["case_id"], []).append(q)
            case_list = list(cases.values())
            shown_cases = 0
            for case_idx, case_questions in enumerate(case_list, start=1):
                visible_questions = (
                    [q for q in case_questions if q["result"] != "correct"]
                    if hide_correct else case_questions
                )
                if not visible_questions:
                    continue
                shown_cases += 1
                header = f"{SECTION_LABELS[section]} case {case_idx} of {len(case_list)}"
                if section == "core":
                    earned, max_points = _core_case_score(case_questions)
                    if max_points > 0:
                        pct = earned / max_points * 100
                        header += f" — {earned:.1f}/{max_points:.0f} ({pct:.0f}%)"
                else:
                    score_pct = _case_score_pct(case_questions)
                    if score_pct is not None:
                        header += f" — {score_pct:.0f}%"
                with st.container(border=True):
                    st.markdown(f"#### {header}")
                    first_q = case_questions[0]
                    st.caption(
                        f"{first_q['source']} · Chapter {first_q['chapter_number']}: "
                        f"{first_q['chapter_title']}"
                    )
                    if first_q.get("clinical_vignette"):
                        st.info(first_q["clinical_vignette"])
                    for q in visible_questions:
                        _render_custom_review_question(
                            test_id, q, label=f"Q{q['q_number']}",
                            expanded=compact and q["result"] in ("incorrect", "partial"),
                        )
            if shown_cases == 0:
                st.info("No partial, incorrect, skipped, or unrated cases in this section.")


def _new_book_import_tab(import_type: str) -> None:
    """Shared UI for MRQ / Short Cases / CORE Cases import tabs."""
    from core.new_book_import import (
        make_session_id, load_session, delete_session,
        get_clarification_questions, run_pass1, run_pass2,
    )

    _type_label = {"mrq": "MRQs", "sc": "Short Cases", "core": "CORE Cases"}[import_type]
    sk = f"nim_{import_type}"   # session-state key prefix

    _secret_key = ""
    try:
        _secret_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        _gh_token   = st.secrets.get("GITHUB_TOKEN", "")
        _gh_repo    = st.secrets.get("GITHUB_REPO", "razzvannastase-ctrl/EDIR_Prep")
    except Exception:
        _gh_token = _gh_repo = ""

    st.markdown(
        f"Import any radiology book and generate EDiR-style **{_type_label}** from its content.  \n"
        "Progress is saved after every chapter — you can safely close and resume later."
    )

    # ── Check for an existing session ─────────────────────────────────────────
    sid     = st.session_state.get(f"{sk}_sid")
    session = load_session(sid) if sid else None
    running = st.session_state.get(f"{sk}_running")

    if session and running is None and session.get("status") not in ("pass2_complete",):
        st.info(
            f"Existing session found: **{session.get('source', '?')}**  \n"
            f"Status: `{session['status'].replace('_', ' ')}`"
        )
        c1, c2 = st.columns(2)
        with c1:
            st.button("Continue this session", key=f"{sk}_keep")
        with c2:
            if st.button("Clear & start new", key=f"{sk}_clear"):
                delete_session(sid)
                for k in [f"{sk}_sid", f"{sk}_running",
                           f"{sk}_pdf_val", f"{sk}_src_val",
                           f"{sk}_api_val", f"{sk}_instr_val",
                           f"{sk}_answers_val", f"{sk}_api_val2"]:
                    st.session_state.pop(k, None)
                st.rerun()
        st.divider()

    # Re-read after potential clear
    sid     = st.session_state.get(f"{sk}_sid")
    session = load_session(sid) if sid else None
    running = st.session_state.get(f"{sk}_running")  # re-read in case clear changed it

    # ── IDLE — show input form ─────────────────────────────────────────────────
    if session is None and not running:
        pdf_in  = st.text_input("PDF path", placeholder="C:/path/to/book.pdf", key=f"{sk}_pdf")
        src_in  = st.text_input("Source / book name",
                                placeholder="e.g. Radiology Review Manual", key=f"{sk}_src")
        api_in  = st.text_input("Anthropic API key", value=_secret_key,
                                type="password", key=f"{sk}_api")
        st.caption(
            "**Book-specific instructions** (optional) — tell Claude anything that helps: "
            "pages to skip (front matter), chapter structure, image layout, etc."
        )
        instr_in = st.text_area(
            "Instructions", height=110, key=f"{sk}_instr",
            placeholder=(
                "e.g. Skip pages 1–15 (front matter). "
                "Cases start on page 16. "
                "Each case: 2 image pages then 1 answer page."
            ),
        )
        can = bool(pdf_in.strip() and src_in.strip() and api_in.strip())
        if st.button("▶  Start — Pass 1 (extract)", type="primary",
                     disabled=not can, key=f"{sk}_start"):
            new_sid = make_session_id(pdf_in.strip(), src_in.strip(), import_type)
            st.session_state[f"{sk}_sid"]      = new_sid
            st.session_state[f"{sk}_running"]  = "pass1"
            st.session_state[f"{sk}_pdf_val"]  = pdf_in.strip().strip('"').strip("'")
            st.session_state[f"{sk}_src_val"]  = src_in.strip()
            st.session_state[f"{sk}_api_val"]  = api_in.strip()
            st.session_state[f"{sk}_instr_val"]= instr_in.strip()
            st.rerun()
        return

    # ── RUNNING PASS 1 ────────────────────────────────────────────────────────
    if running == "pass1":
        pdf_val   = st.session_state.get(f"{sk}_pdf_val", "")
        src_val   = st.session_state.get(f"{sk}_src_val", "")
        api_val   = st.session_state.get(f"{sk}_api_val", _secret_key)
        instr_val = st.session_state.get(f"{sk}_instr_val", "")
        cur_sid   = st.session_state[f"{sk}_sid"]

        st.info(f"Running Pass 1 for **{src_val}** — please wait…")
        prog_bar = st.progress(0.0)
        status_pl = st.empty()

        def _cb1(msg: str, frac):
            if frac is not None:
                prog_bar.progress(min(float(frac), 1.0))
            status_pl.text(msg)

        ok1, msg1 = run_pass1(pdf_val, api_val, src_val, import_type,
                               instr_val, cur_sid, _cb1)
        st.session_state[f"{sk}_running"] = None
        if ok1:
            prog_bar.progress(1.0)
            st.success(msg1)
        else:
            st.error(f"Pass 1 failed: {msg1}")
        st.rerun()
        return

    # ── PASS 1 COMPLETE — clarification + trigger Pass 2 ──────────────────────
    if session.get("status") == "pass1_complete" and running is None:
        src = session.get("source", "?")
        n_chs  = len(session.get("pass1_results", {}))
        n_imgs = sum(len(r.get("images", [])) for r in session["pass1_results"].values())
        st.success(f"Pass 1 complete — **{src}**")
        st.markdown(f"Extracted **{n_chs}** chapter(s) · **{n_imgs}** clinical image(s) found.")

        all_q = get_clarification_questions(sid)
        if all_q:
            st.markdown("**Claude's clarification questions:**")
            for i, q_txt in enumerate(all_q, 1):
                st.markdown(f"**{i}.** {q_txt}")
            answers = st.text_area(
                "Your answers (address each question above, or leave blank to proceed):",
                height=140, key=f"{sk}_answers",
            )
        else:
            st.markdown("*Claude has no clarification questions — ready to generate.*")
            answers = ""

        api_in2 = st.text_input("Anthropic API key", value=_secret_key,
                                 type="password", key=f"{sk}_api2")
        if st.button("⚡  Generate — Pass 2", type="primary", key=f"{sk}_gen"):
            st.session_state[f"{sk}_running"]     = "pass2"
            st.session_state[f"{sk}_answers_val"] = answers
            st.session_state[f"{sk}_api_val2"]    = api_in2.strip()
            st.rerun()
        return

    # ── RUNNING PASS 2 ────────────────────────────────────────────────────────
    if running == "pass2":
        cur_sid  = st.session_state[f"{sk}_sid"]
        ans_val  = st.session_state.get(f"{sk}_answers_val", "")
        api_val2 = st.session_state.get(f"{sk}_api_val2", _secret_key)
        src2     = (load_session(cur_sid) or {}).get("source", "?")

        st.info(f"Running Pass 2 for **{src2}** — please wait…")
        prog_bar2 = st.progress(0.0)
        status_pl2 = st.empty()

        def _cb2(msg: str, frac):
            if frac is not None:
                prog_bar2.progress(min(float(frac), 1.0))
            status_pl2.text(msg)

        ok2, msg2 = run_pass2(cur_sid, api_val2, ans_val, _gh_token, _gh_repo, _cb2)
        st.session_state[f"{sk}_running"] = None
        if ok2:
            prog_bar2.progress(1.0)
            st.success(msg2)
            st.balloons()
        else:
            st.error(f"Pass 2 failed: {msg2}")
        st.rerun()
        return

    # ── PASS 2 PARTIAL — offer resume ─────────────────────────────────────────
    if session.get("status") == "pass2_partial" and running is None:
        done    = set(session.get("pass2_completed", []))
        pending = set(session.get("pass1_results", {}).keys()) - done
        st.warning(
            f"Import partially complete for **{session.get('source')}** — "
            f"{len(done)} chapter(s) done, {len(pending)} remaining."
        )
        api_r = st.text_input("Anthropic API key", value=_secret_key,
                               type="password", key=f"{sk}_api_r")
        if st.button("Resume Pass 2", type="primary", key=f"{sk}_resume_p2"):
            st.session_state[f"{sk}_running"]     = "pass2"
            st.session_state[f"{sk}_api_val2"]    = api_r.strip()
            st.session_state[f"{sk}_answers_val"] = session.get("user_answers", "")
            st.rerun()
        if st.button("Clear & start fresh", key=f"{sk}_clear2"):
            delete_session(sid)
            for k in [f"{sk}_sid", f"{sk}_running"]:
                st.session_state.pop(k, None)
            st.rerun()
        return

    # ── DONE ─────────────────────────────────────────────────────────────────
    if session.get("status") == "pass2_complete":
        st.success(f"Import complete — **{session.get('source')}**")
        # Show chapter mapping with any forced assignments
        mapping = session.get("chapter_mapping", [])
        forced  = [m for m in mapping if m.get("match") == "forced"]
        if forced:
            st.warning(
                "The following chapters were force-assigned (no exact match found). "
                "Review them in the Admin panel."
            )
            for m in forced:
                st.markdown(
                    f"- **{m['new_title']}** → assigned to **{m['db_chapter_title']}** (forced)"
                )
        if st.button("Clear & start new import", key=f"{sk}_done_clear"):
            delete_session(sid)
            for k in [f"{sk}_sid", f"{sk}_running"]:
                st.session_state.pop(k, None)
            st.rerun()


def view_import():
    st.header("Import PDF")

    tab_eg, tab_mrq, tab_sc, tab_core = st.tabs([
        "📚 Essential Guide (Legacy)",
        "🧠 MRQ Import",
        "🔬 Short Cases Import",
        "🏥 CORE Cases Import",
    ])

    # ── Essential Guide (Legacy) ───────────────────────────────────────────────
    with tab_eg:
        st.markdown(
            "Sends every page of the original EDiR PDF to Claude Vision to extract "
            "**CORE Cases, Short Cases, and MRQs**, then crops clinical images and "
            "extracts video links — all in one run.  \n"
            "This clears the existing database and re-imports everything from scratch.  \n"
            "**Cost estimate:** ~305 pages × \\$0.003 ≈ \\$1 USD."
        )

        pdf_path_input = st.text_input(
            "PDF path",
            placeholder="C:/path/to/EDiR_Complete.pdf",
            help="Full path to the original 305-page EDiR PDF on this machine.",
            key="eg_pdf_path",
        )

        _secret_key = ""
        try:
            _secret_key = st.secrets.get("ANTHROPIC_API_KEY", "")
        except Exception:
            pass
        api_key_input = st.text_input(
            "Anthropic API key",
            value=_secret_key,
            type="password",
            help="API key for Claude Vision. Leave blank to use ANTHROPIC_API_KEY from secrets.toml.",
            key="eg_api_key",
        )

        if has_data():
            st.warning("Re-importing will delete **all** existing cases, questions, ratings, and images.")

        pdf_path_clean = pdf_path_input.strip().strip('"').strip("'")
        can_run = bool(pdf_path_clean and api_key_input)
        if st.button("Import PDF", type="primary", disabled=not can_run, key="eg_import_btn"):
            from core.vision_import import run_vision_import

            prog   = st.progress(0.0)
            status = st.empty()

            def _cb(msg: str, frac):
                if frac is not None:
                    prog.progress(min(float(frac), 1.0))
                status.text(msg)

            ok, msg = run_vision_import(pdf_path_clean, api_key_input, _cb)
            prog.progress(1.0)
            if ok:
                status.text("Done.")
                st.success(msg)
                st.balloons()
            else:
                st.error(f"Import failed: {msg}")

        st.markdown("---")
        st.subheader("Clean Up Answer-Page Images")
        st.markdown(
            "Removes any images sourced from **answer pages** that are incorrectly "
            "showing in the question view.  \n"
            "**Free — no API calls.** Reads only PDF bookmarks."
        )
        if st.button("Clean Up Images", disabled=not bool(pdf_path_clean), key="eg_cleanup_btn"):
            from core.reextract_images import cleanup_answer_images

            prog3   = st.progress(0.0)
            status3 = st.empty()

            def _cb3(msg: str, frac):
                if frac is not None:
                    prog3.progress(min(float(frac), 1.0))
                status3.text(msg)

            ok3, msg3 = cleanup_answer_images(pdf_path_clean, _cb3)
            prog3.progress(1.0)
            if ok3:
                status3.text("Done.")
                st.success(msg3)
            else:
                st.error(f"Cleanup failed: {msg3}")

        st.markdown("---")
        st.subheader("Re-extract Images Only")
        st.markdown(
            "Fixes wrong image assignments without re-importing text or answers.  \n"
            "Use this if images appear on the wrong questions after an import.  \n"
            "**All question text and answers are preserved.**"
        )
        if st.button("Re-extract Images",
                     disabled=not bool(pdf_path_clean and api_key_input),
                     key="eg_reextract_btn"):
            from core.reextract_images import run_image_reextraction

            prog2   = st.progress(0.0)
            status2 = st.empty()

            def _cb2(msg: str, frac):
                if frac is not None:
                    prog2.progress(min(float(frac), 1.0))
                status2.text(msg)

            ok2, msg2 = run_image_reextraction(pdf_path_clean, api_key_input, _cb2)
            prog2.progress(1.0)
            if ok2:
                status2.text("Done.")
                st.success(msg2)
            else:
                st.error(f"Re-extraction failed: {msg2}")

    # ── New book import tabs ───────────────────────────────────────────────────
    with tab_mrq:
        _new_book_import_tab("mrq")

    with tab_sc:
        _new_book_import_tab("sc")

    with tab_core:
        _new_book_import_tab("core")


def view_admin():
    from core.github_sync import push_db, push_image
    import time as _time

    st.header("Admin Panel")

    # ── Process pending image action (MUST run before any widget renders) ──────
    _pending_msg = None
    if "_admin_img_action" in st.session_state:
        act = st.session_state.pop("_admin_img_action")
        if act["type"] == "remove":
            lst = st.session_state.get(act["state_key"], [])
            st.session_state[act["state_key"]] = [x for j, x in enumerate(lst) if j != act["idx"]]
            st.session_state.pop(act.get("crop_key", "___none___"), None)
        elif act["type"] == "toggle_crop":
            ck = act["crop_key"]
            st.session_state[ck] = not st.session_state.get(ck, False)
        _pending_msg = act.get("msg")
    if _pending_msg:
        st.success(_pending_msg)

    # ── GitHub config ─────────────────────────────────────────────────────────
    try:
        gh_token = st.secrets.get("GITHUB_TOKEN", "")
        gh_repo  = st.secrets.get("GITHUB_REPO", "razzvannastasa-ctrl/EDIR_Prep")
    except Exception:
        gh_token = gh_repo = ""

    if not gh_token:
        st.warning(
            "Add `GITHUB_TOKEN` (PAT with `repo` scope) to your Streamlit secrets "
            "to enable pushing edits back to GitHub. Edits will still save locally."
        )

    tab_edit, tab_add = st.tabs(["✏️ Edit Questions", "➕ Add Question"])

    # ══════════════════════════════════════════════════════════════════════════
    with tab_add:
        st.subheader("Add New Question")
        a1, a2, a3 = st.columns(3)
        with a1:
            add_sec_map   = {"CORE": "core", "Short Cases": "sc", "MRQs": "mrq"}
            add_sec_lbl   = st.selectbox("Section", list(add_sec_map.keys()), key="add_f_sec")
            add_sec       = add_sec_map[add_sec_lbl]
        with a2:
            add_chapters  = get_chapters()
            if not add_chapters:
                st.info("No chapters in DB yet. Import a PDF first.")
                add_chapters = []
            add_ch_map    = {f"Ch {c['number']}: {c['title']}": dict(c) for c in add_chapters}
            add_ch_lbl    = st.selectbox("Chapter", list(add_ch_map.keys()), key="add_f_ch") if add_ch_map else None
            add_ch        = add_ch_map[add_ch_lbl] if add_ch_lbl else None
        with a3:
            existing_src  = get_sources() or []
            add_src       = st.text_input("Source", value=existing_src[0] if existing_src else "Essential Guide",
                                          key="add_f_src")

        if add_ch:
            # Case picker
            existing_cases = get_cases(add_ch["id"], section=add_sec)
            new_case_lbl   = "➕ New case"
            case_opts      = [new_case_lbl] + [
                f"C{c['case_number']} — {(c['clinical_vignette'] or '')[:60]}"
                for c in existing_cases
            ]
            sel_case_lbl = st.selectbox("Case", case_opts, key="add_f_case_pick")

            if sel_case_lbl == new_case_lbl:
                add_vignette = st.text_area(
                    "Clinical vignette (new case)", height=80, key="add_vignette",
                )
                add_case_id = None
            else:
                cidx         = case_opts.index(sel_case_lbl) - 1
                add_case_id  = existing_cases[cidx]["id"]
                add_vignette = None

            st.markdown("---")
            add_q_text = st.text_area("Question text *", height=120, key="add_q_text")

            if add_sec != "mrq":
                add_vignette_shared = st.text_area(
                    "Clinical vignette (shared by all Qs in this case)",
                    value=add_vignette or "", height=70, key="add_vig_shared",
                    help="Only used when creating a new case",
                ) if sel_case_lbl == new_case_lbl else None
            else:
                add_vignette_shared = None

            add_qtype_lbl = st.selectbox("Question type", ["Free text", "Multiple choice"],
                                         key="add_q_type")
            add_q_type    = "free_text" if add_qtype_lbl == "Free text" else "multiple_choice"

            add_options = []
            add_correct = []
            if add_q_type == "multiple_choice":
                st.markdown("**Options** (one per line)")
                add_opts_text = st.text_area("Options", height=100, key="add_opts",
                                             label_visibility="collapsed")
                add_options   = [o.strip() for o in add_opts_text.splitlines() if o.strip()]
                if add_options:
                    add_corr_sel = st.multiselect("Correct options", add_options, key="add_correct")
                    add_correct  = [add_options.index(o) for o in add_corr_sel if o in add_options]
                add_ans_text = ""
            else:
                add_ans_text = st.text_area("Answer text", height=100, key="add_ans_text")

            add_explanation = st.text_area("Explanation", height=80, key="add_explanation")

            if st.button("💾 Add Question", type="primary", key="add_q_btn"):
                if not add_q_text.strip():
                    st.error("Question text is required.")
                else:
                    # Create new case if needed
                    if add_case_id is None:
                        next_cn     = get_next_case_number(add_ch["id"], add_sec)
                        vig_to_save = (add_vignette_shared or add_vignette or "").strip() or None
                        add_case_id = insert_case(
                            add_ch["id"], next_cn, vig_to_save,
                            section=add_sec, source=add_src.strip() or "Essential Guide",
                        )
                    next_qn = get_next_q_number(add_case_id)
                    new_qid = insert_question(
                        add_case_id, next_qn, add_q_text.strip(), add_q_type,
                        add_options if add_q_type == "multiple_choice" else None,
                        [],
                    )
                    insert_answer(
                        new_qid,
                        add_ans_text.strip() if add_q_type != "multiple_choice" else "",
                        add_correct if add_q_type == "multiple_choice" else None,
                        add_explanation.strip() or None,
                        [],
                    )
                    if gh_token and gh_repo:
                        try:
                            push_db(gh_token, gh_repo, DB_PATH)
                            st.success(f"Question added (Q{next_qn}) and pushed to GitHub.")
                        except Exception as e:
                            st.warning(f"Saved locally — GitHub push failed: {e}")
                    else:
                        st.success(f"Question added (Q{next_qn}) locally.")

    # ══════════════════════════════════════════════════════════════════════════
    with tab_edit:
        # ── Filters ───────────────────────────────────────────────────────────
        f1, f2, f3 = st.columns(3)
        with f1:
            sec_map   = {"All sections": None, "CORE": "core", "Short Cases": "sc", "MRQs": "mrq"}
            sec_label = st.selectbox("Section", list(sec_map.keys()), key="admin_f_sec")
            sec_val   = sec_map[sec_label]
        with f2:
            chapters  = get_chapters()
            ch_map    = {"All chapters": None, **{f"Ch {c['number']}: {c['title']}": c["id"] for c in chapters}}
            ch_label  = st.selectbox("Chapter", list(ch_map.keys()), key="admin_f_ch")
            ch_val    = ch_map[ch_label]
        with f3:
            sources   = get_sources()
            src_map   = {"All sources": None, **{s: s for s in sources}}
            src_label = st.selectbox("Source", list(src_map.keys()), key="admin_f_src")
            src_val   = src_map[src_label]

        # ── Case filter ───────────────────────────────────────────────────────
        all_rows = admin_get_questions(sec_val, ch_val, src_val)
        if not all_rows:
            st.info("No questions match the current filter.")
        else:
            seen_cids: set = set()
            case_list: list[tuple] = []
            for r in all_rows:
                cid = r["case_id"]
                if cid not in seen_cids:
                    seen_cids.add(cid)
                    if r["section"] == "mrq":
                        lbl = f"MRQ Group {r['case_number']}"
                    else:
                        vig     = (r["clinical_vignette"] or "").strip()
                        preview = f" — {vig[:45]}" if vig else ""
                        lbl     = f"C{r['case_number']}{preview}"
                    case_list.append((cid, lbl))

            if len(case_list) > 1:
                case_labels = ["All cases"] + [lbl for _, lbl in case_list]
                n_cl        = len(case_labels)
                raw_ci      = st.session_state.get("admin_f_case", 0)
                cur_ci      = raw_ci if isinstance(raw_ci, int) and 0 <= raw_ci < n_cl else 0
                sel_ci      = st.selectbox("Case", range(n_cl), index=cur_ci,
                                           format_func=lambda i: case_labels[i],
                                           key="admin_f_case")
                if sel_ci == 0:
                    rows = list(all_rows)
                else:
                    sel_cid = case_list[sel_ci - 1][0]
                    rows    = [r for r in all_rows if r["case_id"] == sel_cid]
            else:
                rows = list(all_rows)

            if not rows:
                st.info("No questions match the current filter.")
            else:
                # ── Question selector ──────────────────────────────────────────
                row_by_id = {r["id"]: dict(r) for r in rows}
                q_ids     = [r["id"] for r in rows]
                labels    = [
                    f"[{r['section'].upper()}] Ch{r['chapter_number']} C{r['case_number']} Q{r['q_number']} — {r['question_text'][:70]}"
                    for r in rows
                ]
                n_rows  = len(q_ids)
                raw_idx = st.session_state.get("admin_q_sel", 0)
                cur_idx = raw_idx if isinstance(raw_idx, int) and 0 <= raw_idx < n_rows else 0

                sel_idx  = st.selectbox(
                    f"{len(rows)} questions", range(n_rows), index=cur_idx,
                    format_func=lambda i: labels[i], key="admin_q_sel",
                )
                sel_q_id = q_ids[sel_idx]
                q    = row_by_id[sel_q_id]
                q_id = sel_q_id

                def _admin_imgs(paths_json):
                    return [p for p in json.loads(paths_json or "[]") if "crops" in p]

                if st.session_state.get("_admin_loaded_qid") != q_id:
                    st.session_state._admin_loaded_qid = q_id
                    st.session_state._admin_q_images   = _admin_imgs(q.get("page_images"))
                    _ans = get_answer(q_id)
                    st.session_state._admin_a_images   = _admin_imgs(_ans["page_images"] if _ans else None)

                ans = dict(get_answer(q_id) or {})

                st.markdown("---")
                st.subheader(f"Q{q['q_number']} · {q['section'].upper()} · Ch{q['chapter_number']}: {q['chapter_title']}")

                new_q_text = st.text_area("Question text", value=q["question_text"],
                                          height=150, key=f"admin_qt_{q_id}")

                if q["section"] != "mrq":
                    new_vignette = st.text_area(
                        "Clinical vignette (shared by all questions in this case)",
                        value=q.get("clinical_vignette") or "", height=80,
                        key=f"admin_vig_{q['case_id']}",
                    )
                else:
                    new_vignette = None

                q_type      = q["q_type"]
                options_raw = json.loads(q["options"]) if q.get("options") else []
                correct_raw = json.loads(ans["correct_options"]) if ans.get("correct_options") else []

                if q_type == "multiple_choice":
                    st.markdown("**Options** (one per line)")
                    opts_text   = st.text_area("Options list", value="\n".join(options_raw), height=130,
                                               key=f"admin_opts_{q_id}", label_visibility="collapsed")
                    new_options = [o.strip() for o in opts_text.splitlines() if o.strip()]
                    valid_defaults = [new_options[i] for i in correct_raw if i < len(new_options)]
                    correct_sel    = st.multiselect("Correct options", new_options,
                                                    default=valid_defaults, key=f"admin_correct_{q_id}")
                    new_correct    = [new_options.index(o) for o in correct_sel if o in new_options]
                    new_ans_text   = ans.get("answer_text") or ""
                else:
                    new_options  = options_raw
                    new_correct  = correct_raw
                    new_ans_text = st.text_area("Answer text", value=ans.get("answer_text") or "",
                                                height=120, key=f"admin_ans_{q_id}")

                new_explanation = st.text_area("Explanation", value=ans.get("explanation") or "",
                                               height=80, key=f"admin_exp_{q_id}")

                st.markdown("**Video links** (one URL per line)")
                video_raw       = json.loads(q.get("video_links") or "[]")
                vlinks_text     = st.text_area("Video links list", value="\n".join(video_raw), height=80,
                                               key=f"admin_vl_{q_id}", label_visibility="collapsed")
                new_video_links = [v.strip() for v in vlinks_text.splitlines() if v.strip()]

                try:
                    from streamlit_cropper import st_cropper
                    from PIL import Image as _PILImage
                    _cropper_ok = True
                except ImportError:
                    _cropper_ok = False

                def _image_block(label: str, state_key: str, prefix: str):
                    st.markdown(f"**{label}**")
                    img_list = st.session_state[state_key]
                    for i, img_path in enumerate(list(img_list)):
                        p        = Path(img_path) if Path(img_path).is_absolute() else _APP_DIR / img_path
                        crop_key = f"_admin_crop_{prefix}_{q_id}_{i}"
                        c1, c2, c3 = st.columns([5, 1, 1])
                        with c1:
                            if p.exists():
                                st.image(str(p), width=260)
                            else:
                                st.caption(f"Missing: {img_path}")
                        with c2:
                            st.markdown("<br><br>", unsafe_allow_html=True)
                            if _cropper_ok and p.exists():
                                cropping  = st.session_state.get(crop_key, False)
                                label_btn = "✕ crop" if cropping else "✂"
                                if st.button(label_btn, key=f"admin_crop_btn_{prefix}_{q_id}_{i}",
                                             help="Toggle crop editor"):
                                    st.session_state["_admin_img_action"] = {
                                        "type": "toggle_crop", "crop_key": crop_key,
                                    }
                                    st.rerun()
                        with c3:
                            st.markdown("<br><br>", unsafe_allow_html=True)
                            if st.button("✕", key=f"admin_rm_{prefix}_{q_id}_{i}", help="Remove"):
                                st.session_state["_admin_img_action"] = {
                                    "type": "remove", "state_key": state_key,
                                    "idx": i, "crop_key": crop_key,
                                }
                                st.rerun()
                        if _cropper_ok and p.exists() and st.session_state.get(crop_key, False):
                            _src    = _PILImage.open(str(p))
                            cropped = st_cropper(_src, realtime_update=True, box_color="#C2185B",
                                                 key=f"admin_cropper_{prefix}_{q_id}_{i}")
                            st.image(cropped, caption="Preview", width=260)
                            if st.button("💾 Save crop", key=f"admin_save_crop_{prefix}_{q_id}_{i}",
                                         type="primary"):
                                cropped.save(str(p))
                                if gh_token and gh_repo:
                                    try:
                                        rp = img_path if not Path(img_path).is_absolute() else \
                                            img_path.replace(str(_APP_DIR).replace("\\", "/") + "/", "")
                                        push_image(gh_token, gh_repo, p, rp)
                                    except Exception as e:
                                        st.warning(f"Saved locally, GitHub push failed: {e}")
                                st.session_state["_admin_img_action"] = {
                                    "type": "toggle_crop", "crop_key": crop_key,
                                    "msg": "Crop saved.",
                                }
                                st.rerun()
                    return st.file_uploader(f"Add image to {label.lower()}", type=["png", "jpg", "jpeg"],
                                            key=f"admin_upl_{prefix}_{q_id}")

                uploaded_q_img = _image_block("Question images", "_admin_q_images", "q")
                uploaded_a_img = _image_block("Answer images",   "_admin_a_images", "a")

                # ── Save button ────────────────────────────────────────────────
                st.markdown("---")
                if st.button("Save & Push to GitHub", type="primary", use_container_width=True):
                    crop_dir = _APP_DIR / "data" / "crops"
                    crop_dir.mkdir(parents=True, exist_ok=True)

                    final_q_images = list(st.session_state._admin_q_images)
                    if uploaded_q_img:
                        fname     = f"admin_q{q_id}_{int(_time.time())}.png"
                        img_local = crop_dir / fname
                        img_local.write_bytes(uploaded_q_img.getvalue())
                        final_q_images.append(f"data/crops/{fname}")
                        if gh_token and gh_repo:
                            push_image(gh_token, gh_repo, img_local, f"data/crops/{fname}")

                    final_a_images = list(st.session_state._admin_a_images)
                    if uploaded_a_img:
                        fname     = f"admin_a{q_id}_{int(_time.time())}.png"
                        img_local = crop_dir / fname
                        img_local.write_bytes(uploaded_a_img.getvalue())
                        final_a_images.append(f"data/crops/{fname}")
                        if gh_token and gh_repo:
                            push_image(gh_token, gh_repo, img_local, f"data/crops/{fname}")

                    st.session_state._admin_q_images = final_q_images
                    st.session_state._admin_a_images = final_a_images

                    admin_update_question(
                        q_id, new_q_text,
                        new_options if q_type == "multiple_choice" else None,
                        final_q_images, new_video_links,
                    )
                    admin_update_answer(
                        q_id,
                        answer_text     = new_ans_text    if q_type != "multiple_choice" else None,
                        correct_options = new_correct     if q_type == "multiple_choice" else None,
                        explanation     = new_explanation,
                        page_images     = final_a_images,
                    )
                    if new_vignette is not None:
                        admin_update_vignette(q["case_id"], new_vignette)

                    if gh_token and gh_repo:
                        try:
                            push_db(gh_token, gh_repo, DB_PATH)
                            st.success("Saved and pushed to GitHub.")
                        except Exception as e:
                            st.warning(f"Saved locally, but GitHub push failed: {e}")
                    else:
                        st.success("Saved locally (configure GITHUB_TOKEN to also push to GitHub).")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

section = st.session_state.section

if section in ("core_cases", "short_cases", "mrqs"):
    view = st.session_state.core_view
    if view == "chapters":
        view_chapters()
    elif view == "cases":
        view_cases()
    elif view == "start":
        view_case_start()
    elif view == "question":
        view_question()
    elif view == "review":
        view_review()
    elif view == "learning_summary":
        view_learning_summary()

elif section == "custom":
    custom_view = st.session_state.custom_view
    if custom_view == "dashboard":
        view_custom_dashboard()
    elif custom_view == "test":
        view_custom_test()
    elif custom_view == "review":
        view_custom_results(compact=False)
    elif custom_view == "summary":
        view_custom_results(compact=True)

elif section == "import_pdf":
    view_import()

elif section == "admin":
    view_admin()
