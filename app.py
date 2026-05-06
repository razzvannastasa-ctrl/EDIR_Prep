import time
import json
import datetime
from pathlib import Path

import streamlit as st

from core.database import (
    init_db, has_data,
    get_chapters, get_cases, get_case, get_questions,
    get_answer, get_answers_for_case,
    get_case_stats, get_last_ratings,
    save_attempt, save_rating,
)
from core.parser import run_parser, PDF_PATH

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
    "section":        "core_cases",   # core_cases | short_cases | mrqs | import_pdf
    "core_view":      "chapters",     # chapters | cases | start | question | review
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
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_time(seconds: float) -> str:
    m, s = int(seconds // 60), int(seconds % 60)
    return f"{m:02d}:{s:02d}"


def _submit_case():
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
    st.session_state.case_active = False
    st.session_state.core_view = "review"


_APP_DIR = Path(__file__).parent

def _load_images(paths_json: str | None) -> list[Path]:
    if not paths_json:
        return []
    try:
        paths = []
        for p in json.loads(paths_json):
            if "crops" not in p:
                continue  # skip full-page fallbacks, only show cropped clinical images
            pp = Path(p)
            if not pp.is_absolute():
                pp = _APP_DIR / pp
            paths.append(pp)
        return paths
    except Exception:
        return []


def _show_images(paths: list[Path], caption: str = ""):
    for p in paths:
        if p.exists():
            st.image(str(p), use_container_width=True, caption=caption)
            caption = ""   # only label the first one
        else:
            st.caption(f"Image not rendered yet: {p.name}")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## EDiR Prep")
    st.markdown("---")

    _menu_labels = ["CORE Cases", "Short Cases", "MRQs", "Import PDF"]
    _menu_keys   = ["core_cases", "short_cases", "mrqs", "import_pdf"]
    _current_idx = _menu_keys.index(st.session_state.section)

    _choice = st.radio("", _menu_labels, index=_current_idx, label_visibility="collapsed")
    _chosen_key = _menu_keys[_menu_labels.index(_choice)]

    if _chosen_key != st.session_state.section:
        st.session_state.section = _chosen_key
        if _chosen_key == "core_cases":
            st.session_state.core_view = "chapters"
        st.rerun()

    st.markdown("---")

    # Timer slot — filled later if case is active
    _timer_slot = st.empty()

# ── Timer update (runs every rerun while case is active) ─────────────────────
_remaining: float | None = None
if st.session_state.case_active and st.session_state.timer_start is not None:
    _elapsed   = time.time() - st.session_state.timer_start
    _remaining = max(0.0, st.session_state.timer_limit_s - _elapsed)
    _color     = "#2E7D32" if _remaining > 120 else ("#E65100" if _remaining > 30 else "#C62828")
    _timer_slot.markdown(
        f"<div style='text-align:center'>"
        f"<p style='color:rgba(255,255,255,0.75);margin:0;font-size:0.75em;letter-spacing:1px'>TIME REMAINING</p>"
        f"<p style='font-size:3em;font-weight:bold;color:{_color};margin:0;line-height:1'>"
        f"{_fmt_time(_remaining)}</p></div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════════════════════
# VIEW FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def view_chapters():
    st.header("CORE Cases")

    if not has_data():
        st.info(
            "No content loaded yet.  \n"
            "Go to **Import PDF** in the sidebar to parse the EDiR CORE PDF."
        )
        return

    chapters = get_chapters()
    cols_per_row = 3

    for row_start in range(0, len(chapters), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, ch in zip(cols, chapters[row_start: row_start + cols_per_row]):
            n_cases = len(get_cases(ch["id"]))
            with col:
                with st.container(border=True):
                    st.markdown(f"**Chapter {ch['number']}**")
                    st.markdown(f"### {ch['title']}")
                    st.caption(f"{n_cases} CORE case{'s' if n_cases != 1 else ''}")
                    if st.button("Open →", key=f"open_ch_{ch['id']}",
                                 use_container_width=True):
                        st.session_state.ch_id    = ch["id"]
                        st.session_state.ch_title = ch["title"]
                        st.session_state.core_view = "cases"
                        st.rerun()


def view_cases():
    if st.button("← Chapters"):
        st.session_state.core_view = "chapters"
        st.rerun()

    st.header(f"CORE Cases — {st.session_state.ch_title}")
    cases = get_cases(st.session_state.ch_id)

    if not cases:
        st.warning("No cases found for this chapter.")
        return

    for case in cases:
        attempts, last_at = get_case_stats(case["id"])
        last_ratings = get_last_ratings(case["id"])

        with st.container(border=True):
            c_info, c_btn = st.columns([4, 1])

            with c_info:
                st.markdown(f"**Case {case['case_number']}**")
                vig = (case["clinical_vignette"] or "").strip()
                preview = vig[:140] + ("…" if len(vig) > 140 else "")
                st.caption(preview or "_No vignette available_")

                if attempts:
                    last_str = datetime.datetime.fromtimestamp(last_at).strftime("%d %b %Y")
                    # Summarise last ratings
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

    case      = get_case(st.session_state.case_id)
    questions = get_questions(st.session_state.case_id)
    n_q       = len(questions)

    st.header(f"Case {case['case_number']}  —  {st.session_state.ch_title}")

    # Clinical vignette
    st.subheader("Clinical Presentation")
    vig = (case["clinical_vignette"] or "").strip()
    st.info(vig if vig else "_No vignette available_")

    st.markdown(f"**{n_q} question{'s' if n_q != 1 else ''}** — work through all before time runs out.")

    st.markdown("---")
    c_timer, c_start = st.columns([1, 2])
    with c_timer:
        new_limit = st.number_input(
            "Time limit (min)", min_value=1, max_value=60,
            value=st.session_state.timer_limit_s // 60, step=1,
        )
        st.session_state.timer_limit_s = int(new_limit * 60)
    with c_start:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("▶  Start Case", type="primary", use_container_width=True):
            st.session_state.questions    = [dict(q) for q in questions]
            st.session_state.q_index      = 0
            st.session_state.user_answers = {}
            st.session_state.timer_start  = time.time()
            st.session_state.case_active  = True
            st.session_state.ratings      = {}
            st.session_state.attempt_id   = None
            st.session_state.core_view    = "question"
            st.rerun()


def view_question():
    questions = st.session_state.questions
    q_idx     = st.session_state.q_index
    n_q       = len(questions)

    if not questions:
        st.error("No questions loaded.")
        return

    q    = questions[q_idx]
    q_id = q["id"]

    # Progress bar
    st.progress((q_idx + 1) / n_q,
                text=f"Question {q_idx + 1} of {n_q}")

    col_q, col_img = st.columns([1, 1], gap="large")

    # ── Left: question + answer input ─────────────────────────────────────────
    with col_q:
        st.markdown(f"### Q{q['q_number']}")
        st.markdown(q["question_text"])

        q_type  = q["q_type"]
        saved   = st.session_state.user_answers.get(q_id)
        options = json.loads(q["options"]) if q.get("options") else []

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
            prev_sel = [options[i] for i in (saved or []) if i < len(options)]
            chosen = st.multiselect(
                "Select all that apply:",
                options,
                default=prev_sel,
                key=f"mc_{q_id}",
            )
            st.session_state.user_answers[q_id] = [options.index(c) for c in chosen]

        # Navigation buttons
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
            _show_images(imgs)
        video_links = json.loads(q.get("video_links") or "[]")
        for i, url in enumerate(video_links, 1):
            st.markdown(f"[▶ Video {i}]({url})")

    # ── Timer tick (only runs while case is active) ───────────────────────────
    if st.session_state.case_active:
        if _remaining is not None and _remaining <= 0:
            st.warning("Time's up! Submitting automatically…")
            _submit_case()
            st.rerun()
        else:
            time.sleep(1)
            st.rerun()


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

    for q in questions:
        q_id     = q["id"]
        ans_row  = get_answer(q_id)
        user_ans = st.session_state.user_answers.get(q_id)
        options  = json.loads(q["options"]) if q.get("options") else []
        rating   = st.session_state.ratings.get(q_id)

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
            # ── Question + user answer | Correct answer ───────────────────────
            col_q, col_a = st.columns(2, gap="large")

            with col_q:
                st.markdown("**Question**")
                st.markdown(q["question_text"])
                st.markdown("**Your answer**")

                if q["q_type"] == "free_text":
                    st.markdown(user_ans or "_No answer_")
                elif options:
                    if isinstance(user_ans, int):
                        chosen = [options[user_ans]] if user_ans < len(options) else []
                    elif isinstance(user_ans, list):
                        chosen = [options[i] for i in user_ans if i < len(options)]
                    else:
                        chosen = []
                    if chosen:
                        for c in chosen:
                            st.markdown(f"→ {c}")
                    else:
                        st.markdown("_No answer_")

            with col_a:
                st.markdown("**Correct Answer**")
                if ans_row and ans_row["answer_text"]:
                    st.markdown(ans_row["answer_text"])
                else:
                    st.markdown("_Answer not available_")

                if ans_row and ans_row["explanation"]:
                    st.markdown("**Explanation**")
                    st.markdown(ans_row["explanation"])

            # Cropped clinical images for this question
            imgs = _load_images(q.get("page_images"))
            if imgs:
                _show_images(imgs)

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


def view_import():
    st.header("Import PDF")

    exists = PDF_PATH.exists()
    if exists:
        size_mb = PDF_PATH.stat().st_size / 1_048_576
        st.success(f"EDiR_CORE.pdf found ({size_mb:.1f} MB)")
    else:
        st.warning(
            f"EDiR_CORE.pdf not found.  \n"
            f"Copy it to: `{PDF_PATH}`"
        )

    st.markdown("---")
    st.markdown(
        "**Parsing** extracts all CORE cases, questions, and answers from the PDF "
        "and renders every page as an image.  \n"
        "On first run this can take **2–5 minutes** depending on your machine."
    )

    if has_data():
        st.warning("Re-parsing will delete all existing cases and ratings.")

    if st.button("Parse EDiR_CORE.pdf", type="primary", disabled=not exists):
        prog_bar    = st.progress(0.0)
        status_text = st.empty()

        def _on_progress(msg: str, frac: float):
            prog_bar.progress(min(frac, 1.0))
            status_text.text(msg)

        ok, msg = run_parser(_on_progress)
        prog_bar.progress(1.0)

        if ok:
            st.success(msg)
            st.balloons()
        else:
            st.error(msg)

    # ── Vision enhancement ────────────────────────────────────────────────────
    if has_data():
        st.markdown("---")
        st.markdown("#### Extract images with Claude Vision")
        st.markdown(
            "Replaces full-page screenshots with cropped clinical images "
            "(X-rays, CTs, MRIs) mapped to each question. Runs once; results "
            "are saved locally. Requires an Anthropic API key in secrets."
        )
        if st.button("Run Vision Enhancement", disabled=not has_data()):
            from core.vision import run_vision_enhancement
            api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
            status  = st.empty()
            def _vis_cb(msg, _frac):
                status.text(msg)
            ok2, msg2 = run_vision_enhancement(api_key, _vis_cb)
            if ok2:
                st.success(msg2)
            else:
                st.error(msg2)

        if st.button("Extract Video Links (PDF)", disabled=not has_data()):
            from core.vision import run_doi_extraction
            ok3, msg3 = run_doi_extraction()
            if ok3:
                st.success(msg3)
            else:
                st.error(msg3)

    st.markdown("---")
    st.markdown("#### Short Cases & MRQs")
    st.info(
        "After Short Cases and MRQs PDFs are ready, you will be able to import "
        "them here and practice all three question types."
    )


def view_coming_soon(label: str):
    st.header(label)
    st.info(
        f"**{label}** practice is coming soon.  \n"
        "Focus on CORE Cases for now, then check back here after the next update."
    )


# ══════════════════════════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════════════════════════

section = st.session_state.section

if section == "core_cases":
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

elif section == "short_cases":
    view_coming_soon("Short Cases")

elif section == "mrqs":
    view_coming_soon("MRQs")

elif section == "import_pdf":
    view_import()
