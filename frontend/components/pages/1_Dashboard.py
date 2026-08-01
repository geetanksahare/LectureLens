"""
1_Dashboard.py
---------------------------------------------------------
Home page after login. Shows quick stats and recent activity.
"""

import os
import sys

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.db_manager import get_dashboard_stats, get_lectures_for_user
from components.sidebar import render_sidebar, require_login

st.set_page_config(page_title="Dashboard - LectureLens", page_icon="🏠", layout="wide")

require_login()
render_sidebar()

st.title(f"👋 Welcome back, {st.session_state['username']}")

stats = get_dashboard_stats(st.session_state["user_id"])

col1, col2, col3 = st.columns(3)
col1.metric("Lectures Processed", stats["lecture_count"])
col2.metric(
    "Average Quiz Score",
    f"{stats['avg_quiz_score']:.0f}%" if stats["avg_quiz_score"] is not None else "—",
)
col3.page_link("pages/2_Process_Lecture.py", label="🎬 Process New Lecture", use_container_width=True)

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
                st.page_link(
                    "pages/3_History.py",
                    label="View →",
                    use_container_width=True,
                )
