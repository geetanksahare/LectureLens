"""
LectureLens - Complete Single-File Frontend
---------------------------------------------------------
Everything in one file: Signup, Login, Dashboard, Process Lecture
(audio extraction -> Whisper transcription -> subtitles -> summary
-> 10-question quiz), and History — all navigated via session state
instead of Streamlit's multipage folder structure.

Run from the project root:
    streamlit run frontend/app.py
"""

import os
import sys
import tempfile

import streamlit as st

# Allow "backend.xxx" imports to work when Streamlit runs this file directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.db_manager import (
    init_db,
    create_lecture,
    add_transcript_segments,
    save_quiz_result,
    get_lectures_for_user,
    get_transcript_segments,
    get_quiz_results_for_lecture,
    get_dashboard_stats,
)
from backend.auth.auth_manager import signup, login
from backend.audio_extraction.audio_extractor import extract_audio
from backend.transcription.transcriber import process_audio
from backend.subtitle_generation.subtitle_generator import save_subtitles
from backend.summarization.summarizer import chunk_transcript, summarize_technical, simplify_eli_junior
from backend.quiz_generation.quiz_generator import generate_mcqs, get_weak_areas


TOTAL_MCQS = 10

st.set_page_config(page_title="LectureLens", page_icon="🎓", layout="wide")

# Make sure DB tables exist on every app startup
init_db()


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
def init_state():
    defaults = {
        "logged_in": False,
        "user_id": None,
        "username": None,
        "view": "login",           # login | dashboard | process | history
        # process-lecture results
        "processed": False,
        "last_lecture_id": None,
        "last_segments": None,
        "last_technical_summary": None,
        "last_simple_summary": None,
        "last_mcqs": None,
        "last_srt_path": None,
        "quiz_answers": {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_state()


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------
def format_mmss(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


def render_transcript(segments):
    """Renders a list of segments as timestamped lines. Works with either
    transcriber.py output ('start'/'text') or DB rows ('start_time'/'text')."""
    for seg in segments:
        start = seg.get("start", seg.get("start_time"))
        text = seg.get("text", "")
        st.markdown(f"`[{format_mmss(start)}]` {text}")


def distribute_mcq_counts(num_chunks, total=TOTAL_MCQS):
    base = total // num_chunks
    remainder = total % num_chunks
    counts = [base] * num_chunks
    for i in range(remainder):
        counts[i] += 1
    return counts


def generate_ten_mcqs(chunks):
    counts = distribute_mcq_counts(len(chunks))
    all_mcqs = []
    for chunk, count in zip(chunks, counts):
        if count == 0:
            continue
        qs = generate_mcqs(chunk["text"], chunk["start"], num_questions=count)
        all_mcqs.extend(qs)
    return all_mcqs[:TOTAL_MCQS]


def go_to(view_name):
    st.session_state["view"] = view_name
    st.rerun()


def logout():
    for key in ["logged_in", "user_id", "username", "processed", "last_lecture_id",
                "last_segments", "last_technical_summary", "last_simple_summary",
                "last_mcqs", "last_srt_path", "quiz_answers"]:
        st.session_state.pop(key, None)
    init_state()
    st.session_state["view"] = "login"
    st.rerun()


# ---------------------------------------------------------
# SIDEBAR NAV (only shown once logged in)
# ---------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        st.title("🎓 LectureLens")
        st.caption(f"Logged in as **{st.session_state['username']}**")
        st.divider()

        if st.button("🏠 Dashboard", use_container_width=True):
            go_to("dashboard")
        if st.button("🎬 Process Lecture", use_container_width=True):
            go_to("process")
        if st.button("📜 History", use_container_width=True):
            go_to("history")

        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            logout()


# ---------------------------------------------------------
# VIEW: LOGIN / SIGNUP
# ---------------------------------------------------------
def render_login_signup():
    st.title("🎓 LectureLens")
    st.caption("AI-powered lecture transcription, simplification & quiz generator")

    tab_login, tab_signup = st.tabs(["🔐 Log In", "📝 Sign Up"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In", type="primary", use_container_width=True)

        if submitted:
            ok, message, user = login(username, password)
            if ok:
                st.session_state["logged_in"] = True
                st.session_state["user_id"] = user["id"]
                st.session_state["username"] = user["username"]
                st.session_state["view"] = "dashboard"
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with tab_signup:
        with st.form("signup_form"):
            new_username = st.text_input("Choose a username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Choose a password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            signup_submitted = st.form_submit_button("Create Account", type="primary", use_container_width=True)

        if signup_submitted:
            ok, message = signup(new_username, new_email, new_password, confirm_password)
            if ok:
                st.success(message + " Switch to the Log In tab to continue.")
            else:
                st.error(message)


# ---------------------------------------------------------
# VIEW: DASHBOARD
# ---------------------------------------------------------
def render_dashboard():
    st.title(f"👋 Welcome back, {st.session_state['username']}")

    stats = get_dashboard_stats(st.session_state["user_id"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Lectures Processed", stats["lecture_count"])
    col2.metric(
        "Average Quiz Score",
        f"{stats['avg_quiz_score']:.0f}%" if stats["avg_quiz_score"] is not None else "—",
    )
    with col3:
        st.write("")
        if st.button("🎬 Process New Lecture", type="primary", use_container_width=True):
            go_to("process")

    st.divider()
    st.subheader("📜 Recent Activity")

    lectures = get_lectures_for_user(st.session_state["user_id"])

    if not lectures:
        st.info("You haven't processed any lectures yet. Click 'Process New Lecture' to get started.")
    else:
        for lec in lectures[:5]:
            with st.container(border=True):
                col_a, col_b = st.columns([4, 1])
                with col_a:
                    st.markdown(f"**{lec['filename']}**")
                    st.caption(f"Processed on {lec['processed_at']}")
                with col_b:
                    if st.button("View →", key=f"view_{lec['id']}", use_container_width=True):
                        go_to("history")


# ---------------------------------------------------------
# VIEW: PROCESS LECTURE
# ---------------------------------------------------------
def render_process_lecture():
    st.title("🎬 Process a New Lecture")

    uploaded_file = st.file_uploader(
        "Upload a lecture video/audio file",
        type=["mp4", "mkv", "mov", "mp3", "wav", "m4a"],
    )

    run_button = st.button("🚀 Process Lecture", type="primary", use_container_width=True)

    if run_button:
        if uploaded_file is None:
            st.error("Please upload a file first.")
        else:
            input_suffix = os.path.splitext(uploaded_file.name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=input_suffix) as tmp_input:
                tmp_input.write(uploaded_file.read())
                input_path = tmp_input.name

            extracted_audio_path = input_path + "_extracted.wav"

            try:
                with st.status("Running LectureLens pipeline...", expanded=True) as status:

                    st.write("🎬 Extracting audio...")
                    success, message, _ = extract_audio(input_path, extracted_audio_path)
                    if not success:
                        st.error(f"Audio extraction failed: {message}")
                        st.stop()
                    st.write("✅ Audio extracted")

                    st.write("🎙️ Transcribing with Whisper...")
                    segments = process_audio(extracted_audio_path)
                    st.write(f"✅ {len(segments)} segments transcribed")

                    st.write("📝 Generating subtitles...")
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    subtitle_paths = save_subtitles(segments, filename=base_name)
                    st.write("✅ Subtitles saved")

                    st.write("📚 Chunking transcript...")
                    chunks = chunk_transcript(segments)
                    st.write(f"✅ {len(chunks)} chunks created")

                    st.write("✨ Generating summaries...")
                    technical_parts, simple_parts = [], []
                    for chunk in chunks:
                        technical_parts.append(summarize_technical(chunk["text"]))
                        simple_parts.append(simplify_eli_junior(chunk["text"]))
                    technical_summary = "\n\n".join(technical_parts)
                    simple_summary = "\n\n".join(simple_parts)
                    st.write("✅ Summaries generated")

                    st.write(f"🧠 Generating {TOTAL_MCQS} quiz questions...")
                    mcqs = generate_ten_mcqs(chunks)
                    st.write(f"✅ {len(mcqs)} questions generated")

                    st.write("💾 Saving to your account...")
                    full_transcript = " ".join(seg["text"] for seg in segments)
                    lecture_id = create_lecture(
                        user_id=st.session_state["user_id"],
                        filename=uploaded_file.name,
                        full_transcript=full_transcript,
                        technical_summary=technical_summary,
                        simple_summary=simple_summary,
                        srt_path=subtitle_paths["srt_path"],
                        vtt_path=subtitle_paths["vtt_path"],
                    )
                    add_transcript_segments(lecture_id, segments)
                    st.write("✅ Saved to history")

                    status.update(label="✅ Pipeline complete!", state="complete")

                st.session_state["processed"] = True
                st.session_state["last_lecture_id"] = lecture_id
                st.session_state["last_segments"] = segments
                st.session_state["last_technical_summary"] = technical_summary
                st.session_state["last_simple_summary"] = simple_summary
                st.session_state["last_mcqs"] = mcqs
                st.session_state["last_srt_path"] = subtitle_paths["srt_path"]
                st.session_state["quiz_answers"] = {}

            finally:
                if os.path.exists(input_path):
                    os.remove(input_path)
                if os.path.exists(extracted_audio_path):
                    os.remove(extracted_audio_path)

    if st.session_state["processed"]:
        st.divider()
        tab_transcript, tab_summary, tab_quiz, tab_download = st.tabs(
            ["📝 Transcript", "✨ Summary", "🧠 Quiz", "⬇️ Download .srt"]
        )

        with tab_transcript:
            render_transcript(st.session_state["last_segments"])

        with tab_summary:
            mode = st.radio("View mode", ["Simple (ELI-Junior)", "Technical"], horizontal=True)
            if mode == "Technical":
                st.write(st.session_state["last_technical_summary"])
            else:
                st.write(st.session_state["last_simple_summary"])

        with tab_quiz:
            mcqs = st.session_state["last_mcqs"]
            if not mcqs:
                st.warning("No quiz questions were generated.")
            else:
                with st.form("quiz_form"):
                    for idx, q in enumerate(mcqs, start=1):
                        st.markdown(f"**{idx}. {q['question']}**")
                        options = q.get("options", {})
                        selected = st.radio(
                            "Choose an answer",
                            options=list(options.keys()),
                            format_func=lambda k, opts=options: f"{k}. {opts[k]}",
                            key=f"mcq_{idx}",
                            label_visibility="collapsed",
                        )
                        st.session_state["quiz_answers"][q["question"]] = selected
                        st.divider()
                    submitted = st.form_submit_button("✅ Submit Quiz", type="primary")

                if submitted:
                    quiz_wrapper = {"quiz": [{"mcqs": mcqs}]}
                    weak_areas = get_weak_areas(quiz_wrapper, st.session_state["quiz_answers"])
                    correct = len(mcqs) - len(weak_areas)

                    save_quiz_result(st.session_state["last_lecture_id"], correct, len(mcqs))

                    st.success(f"Score: {correct} / {len(mcqs)} correct (saved to your history)")

                    if weak_areas:
                        st.subheader("📌 Questions you got wrong")
                        for w in weak_areas:
                            st.markdown(
                                f"- **{w['question']}** — you answered `{w['your_answer']}`, "
                                f"correct was `{w['correct_answer']}`"
                            )
                            if w.get("explanation"):
                                st.caption(w["explanation"])
                    else:
                        st.balloons()
                        st.write("All correct! 🎉")

        with tab_download:
            srt_path = st.session_state["last_srt_path"]
            if srt_path and os.path.exists(srt_path):
                with open(srt_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download .srt",
                        data=f.read(),
                        file_name=os.path.basename(srt_path),
                        mime="text/plain",
                        use_container_width=True,
                    )


# ---------------------------------------------------------
# VIEW: HISTORY
# ---------------------------------------------------------
def render_history():
    st.title("📜 Lecture History")

    lectures = get_lectures_for_user(st.session_state["user_id"])

    if not lectures:
        st.info("No lectures processed yet.")
        if st.button("🎬 Process your first lecture"):
            go_to("process")
        return

    lecture_options = {f"{lec['filename']} ({lec['processed_at']})": lec["id"] for lec in lectures}
    selected_label = st.selectbox("Select a past lecture", options=list(lecture_options.keys()))
    selected_id = lecture_options[selected_label]

    selected_lecture = next(lec for lec in lectures if lec["id"] == selected_id)

    st.divider()

    tab_transcript, tab_summary, tab_quiz_history, tab_download = st.tabs(
        ["📝 Transcript", "✨ Summary", "🧠 Quiz History", "⬇️ Download .srt"]
    )

    with tab_transcript:
        segments = get_transcript_segments(selected_id)
        if segments:
            render_transcript(segments)
        else:
            st.info("No timestamped segments stored for this lecture.")

    with tab_summary:
        mode = st.radio("View mode", ["Simple (ELI-Junior)", "Technical"], horizontal=True, key="history_mode")
        if mode == "Technical":
            st.write(selected_lecture["technical_summary"])
        else:
            st.write(selected_lecture["simple_summary"])

    with tab_quiz_history:
        results = get_quiz_results_for_lecture(selected_id)
        if not results:
            st.info("This lecture's quiz hasn't been attempted yet.")
        else:
            for r in results:
                pct = round(r["score"] / r["total_questions"] * 100)
                st.markdown(f"- **{r['score']}/{r['total_questions']}** ({pct}%) — {r['taken_at']}")

    with tab_download:
        srt_path = selected_lecture.get("srt_path")
        if srt_path and os.path.exists(srt_path):
            with open(srt_path, "rb") as f:
                st.download_button(
                    "⬇️ Download .srt",
                    data=f.read(),
                    file_name=os.path.basename(srt_path),
                    mime="text/plain",
                )
        else:
            st.info("Subtitle file not found on disk (it may have been cleared).")


# ---------------------------------------------------------
# MAIN ROUTER
# ---------------------------------------------------------
if not st.session_state["logged_in"]:
    render_login_signup()
else:
    render_sidebar()

    view = st.session_state["view"]
    if view == "dashboard":
        render_dashboard()
    elif view == "process":
        render_process_lecture()
    elif view == "history":
        render_history()
    else:
        render_dashboard()