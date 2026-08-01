"""
3_History.py
---------------------------------------------------------
Lists all past lectures for the logged-in user. Selecting one
reloads its timestamped transcript, summary, and quiz results
from the database.
"""

import os
import sys

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.db_manager import (
    get_lectures_for_user,
    get_transcript_segments,
    get_quiz_results_for_lecture,
)
from components.sidebar import render_sidebar, require_login
from components.transcript_view import render_transcript

st.set_page_config(page_title="History - LectureLens", page_icon="📜", layout="wide")

require_login()
render_sidebar()

st.title("📜 Lecture History")

lectures = get_lectures_for_user(st.session_state["user_id"])

if not lectures:
    st.info("No lectures processed yet.")
    st.page_link("pages/2_Process_Lecture.py", label="🎬 Process your first lecture", icon="🎬")
    st.stop()

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
