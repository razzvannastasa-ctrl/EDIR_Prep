import time
import json
import datetime
from pathlib import Path

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from core.database import (
    init_db, has_data, has_section,
    get_chapters, get_chapters_with_section, get_cases, get_case, get_questions,
    get_answer, get_answers_for_case,
    get_case_stats, get_last_ratings,
    save_attempt, save_rating,
    admin_get_questions, admin_update_question, admin_update_answer, admin_update_vignette,
    DB_PATH,
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
    "section":        "core_cases",   # core_cases | short_cases | mrqs | import_pdf | admin
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

def _db_section() -> str:
    return {"core_cases": "core", "short_cases": "sc", "mrqs": "mrq"}.get(
        st.session_state.section, "core"
    )


def _section_label() -> str:
    return {"core_cases": "CORE Cases", "short_cases": "Short Cases", "mrqs": "MRQs"}.get(
        st.session_state.section, "CORE Cases"
    )


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

    _menu_labels = ["CORE Cases", "Short Cases", "MRQs", "Import PDF", "Admin"]
    _menu_keys   = ["core_cases", "short_cases", "mrqs", "import_pdf", "admin"]
    _current_idx = _menu_keys.index(st.session_state.section)

    _choice = st.radio("Navigation", _menu_labels, index=_current_idx, label_visibility="collapsed")
    _chosen_key = _menu_keys[_menu_labels.index(_choice)]

    if _chosen_key != st.session_state.section:
        st.session_state.section = _chosen_key
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
    label = _section_label()
    sec   = _db_section()
    st.header(label)

    if not has_section(sec):
        st.info(
            f"No {label} content loaded yet.  \n"
            "Go to **Import PDF** in the sidebar to import the EDiR PDF."
        )
        return

    chapters = get_chapters_with_section(sec)
    cols_per_row = 3

    for row_start in range(0, len(chapters), cols_per_row):
        cols = st.columns(cols_per_row)
        for col, ch in zip(cols, chapters[row_start: row_start + cols_per_row]):
            n_cases = len(get_cases(ch["id"], section=sec))
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
    cases = get_cases(st.session_state.ch_id, section=sec)

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
                    st.markdown(f"**MRQ Session — Chapter {st.session_state.ch_title}**")
                    st.caption(f"{n_qs} multiple-choice question{'s' if n_qs != 1 else ''}")
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
        st.header(f"MRQs — Chapter {st.session_state.ch_title}")
    else:
        st.header(f"Case {case['case_number']}  —  {st.session_state.ch_title}")

    # Clinical vignette — not shown for MRQ sessions
    if sec != "mrq":
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
    # Refresh every second while case is active to keep the timer ticking
    if st.session_state.case_active:
        st_autorefresh(interval=1000, key="case_timer")

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

    # ── Auto-submit when time runs out ────────────────────────────────────────
    if st.session_state.case_active and _remaining is not None and _remaining <= 0:
        st.warning("Time's up! Submitting automatically…")
        _submit_case()
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
                elif ans_row and ans_row["correct_options"] and options:
                    correct_indices = json.loads(ans_row["correct_options"])
                    correct_labels = [options[i] for i in correct_indices if i < len(options)]
                    for c in correct_labels:
                        st.markdown(f"→ {c}")
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
    )

    if has_data():
        st.warning("Re-importing will delete **all** existing cases, questions, ratings, and images.")

    pdf_path_clean = pdf_path_input.strip().strip('"').strip("'")
    can_run = bool(pdf_path_clean and api_key_input)
    if st.button("Import PDF", type="primary", disabled=not can_run):
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
    if st.button("Clean Up Images", disabled=not bool(pdf_path_clean)):
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
    if st.button("Re-extract Images", disabled=not bool(pdf_path_clean and api_key_input)):
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

    # ── Filters ───────────────────────────────────────────────────────────────
    f1, f2 = st.columns(2)
    with f1:
        sec_map   = {"All sections": None, "CORE": "core", "Short Cases": "sc", "MRQs": "mrq"}
        sec_label = st.selectbox("Section", list(sec_map.keys()), key="admin_f_sec")
        sec_val   = sec_map[sec_label]
    with f2:
        chapters  = get_chapters()
        ch_map    = {"All chapters": None, **{f"Ch {c['number']}: {c['title']}": c["id"] for c in chapters}}
        ch_label  = st.selectbox("Chapter", list(ch_map.keys()), key="admin_f_ch")
        ch_val    = ch_map[ch_label]

    rows = admin_get_questions(sec_val, ch_val)
    if not rows:
        st.info("No questions match the current filter.")
        return

    # ── Question selector ─────────────────────────────────────────────────────
    row_by_id  = {r["id"]: dict(r) for r in rows}
    label_by_id = {
        r["id"]: f"[{r['section'].upper()}] Ch{r['chapter_number']} · Q{r['q_number']} — {r['question_text'][:80]}"
        for r in rows
    }
    q_ids = [r["id"] for r in rows]
    sel_q_id = st.selectbox(
        f"{len(rows)} questions", q_ids,
        format_func=lambda qid: label_by_id.get(qid, str(qid)),
        key="admin_q_sel",
    )
    q    = row_by_id[sel_q_id]
    q_id = sel_q_id

    def _admin_imgs(paths_json):
        return [p for p in json.loads(paths_json or "[]") if "crops" in p]

    # Reset image lists when question changes
    if st.session_state.get("_admin_loaded_qid") != q_id:
        st.session_state._admin_loaded_qid = q_id
        st.session_state._admin_q_images   = _admin_imgs(q.get("page_images"))
        _ans = get_answer(q_id)
        st.session_state._admin_a_images   = _admin_imgs(_ans["page_images"] if _ans else None)

    ans  = get_answer(q_id)
    ans  = dict(ans) if ans else {}

    st.markdown("---")
    st.subheader(f"Q{q['q_number']} · {q['section'].upper()} · Ch{q['chapter_number']}: {q['chapter_title']}")

    # ── Question text ─────────────────────────────────────────────────────────
    new_q_text = st.text_area("Question text", value=q["question_text"],
                               height=150, key=f"admin_qt_{q_id}")

    # ── Clinical vignette (non-MRQ only) ─────────────────────────────────────
    if q["section"] != "mrq":
        new_vignette = st.text_area(
            "Clinical vignette (shared by all questions in this case)",
            value=q.get("clinical_vignette") or "", height=80,
            key=f"admin_vig_{q['case_id']}",
        )
    else:
        new_vignette = None

    # ── Options / answer ─────────────────────────────────────────────────────
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

    # ── Video links ───────────────────────────────────────────────────────────
    st.markdown("**Video links** (one URL per line)")
    video_raw   = json.loads(q.get("video_links") or "[]")
    vlinks_text = st.text_area("Video links list", value="\n".join(video_raw), height=80,
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
            p = Path(img_path) if Path(img_path).is_absolute() else _APP_DIR / img_path
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
                    cropping = st.session_state.get(crop_key, False)
                    label_btn = "✕ crop" if cropping else "✂"
                    if st.button(label_btn, key=f"admin_crop_btn_{prefix}_{q_id}_{i}",
                                 help="Toggle crop editor"):
                        st.session_state["_admin_img_action"] = {
                            "type": "toggle_crop", "crop_key": crop_key,
                        }
            with c3:
                st.markdown("<br><br>", unsafe_allow_html=True)
                if st.button("✕", key=f"admin_rm_{prefix}_{q_id}_{i}", help="Remove"):
                    st.session_state["_admin_img_action"] = {
                        "type": "remove", "state_key": state_key,
                        "idx": i, "crop_key": crop_key,
                    }

            # Inline cropper
            if _cropper_ok and p.exists() and st.session_state.get(crop_key, False):
                src = _PILImage.open(str(p))
                cropped = st_cropper(src, realtime_update=True, box_color="#C2185B",
                                     key=f"admin_cropper_{prefix}_{q_id}_{i}")
                st.image(cropped, caption="Preview", width=260)
                if st.button("💾 Save crop", key=f"admin_save_crop_{prefix}_{q_id}_{i}",
                             type="primary"):
                    cropped.save(str(p))
                    if gh_token and gh_repo:
                        try:
                            repo_path = img_path if not Path(img_path).is_absolute() else \
                                img_path.replace(str(_APP_DIR).replace("\\", "/") + "/", "")
                            push_image(gh_token, gh_repo, p, repo_path)
                        except Exception as e:
                            st.warning(f"Saved locally, GitHub push failed: {e}")
                    st.session_state["_admin_img_action"] = {
                        "type": "toggle_crop", "crop_key": crop_key,
                        "msg": "Crop saved.",
                    }

        return st.file_uploader(f"Add image to {label.lower()}", type=["png", "jpg", "jpeg"],
                                key=f"admin_upl_{prefix}_{q_id}")

    uploaded_q_img = _image_block("Question images", "_admin_q_images", "q")
    uploaded_a_img = _image_block("Answer images",   "_admin_a_images", "a")

    # ── Save button ───────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("Save & Push to GitHub", type="primary", use_container_width=True):
        crop_dir = _APP_DIR / "data" / "crops"
        crop_dir.mkdir(parents=True, exist_ok=True)

        # Handle uploaded question image
        final_q_images = list(st.session_state._admin_q_images)
        if uploaded_q_img:
            fname     = f"admin_q{q_id}_{int(_time.time())}.png"
            img_local = crop_dir / fname
            img_local.write_bytes(uploaded_q_img.getvalue())
            repo_path = f"data/crops/{fname}"
            final_q_images.append(f"data/crops/{fname}")
            if gh_token and gh_repo:
                push_image(gh_token, gh_repo, img_local, repo_path)

        # Handle uploaded answer image
        final_a_images = list(st.session_state._admin_a_images)
        if uploaded_a_img:
            fname     = f"admin_a{q_id}_{int(_time.time())}.png"
            img_local = crop_dir / fname
            img_local.write_bytes(uploaded_a_img.getvalue())
            repo_path = f"data/crops/{fname}"
            final_a_images.append(f"data/crops/{fname}")
            if gh_token and gh_repo:
                push_image(gh_token, gh_repo, img_local, repo_path)

        # Update session state image lists
        st.session_state._admin_q_images = final_q_images
        st.session_state._admin_a_images = final_a_images

        # Write to SQLite
        admin_update_question(
            q_id, new_q_text,
            new_options if q_type == "multiple_choice" else None,
            final_q_images, new_video_links,
        )
        admin_update_answer(
            q_id,
            answer_text    = new_ans_text   if q_type != "multiple_choice" else None,
            correct_options= new_correct    if q_type == "multiple_choice" else None,
            explanation    = new_explanation,
            page_images    = final_a_images,
        )
        if new_vignette is not None:
            admin_update_vignette(q["case_id"], new_vignette)

        # Push DB to GitHub
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

elif section == "import_pdf":
    view_import()

elif section == "admin":
    view_admin()
