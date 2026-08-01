"""
sidebar.py
---------------------------------------------------------
Shared sidebar shown on every logged-in page: welcome message,
navigation links, and a logout button.
"""

import streamlit as st


def render_sidebar():
    with st.sidebar:
        st.title("🎓 LectureLens")

        if st.session_state.get("logged_in"):
            st.caption(f"Logged in as **{st.session_state['username']}**")
            st.divider()

            st.page_link("app.py", label="🔓 Log out (go to login page)")

            if st.button("🚪 Log out", use_container_width=True):
                for key in ["logged_in", "user_id", "username"]:
                    st.session_state.pop(key, None)
                st.switch_page("app.py")


def require_login():
    """
    Call this at the top of every protected page.
    Stops execution and shows a message if the user isn't logged in.
    """
    if not st.session_state.get("logged_in"):
        st.warning("Please log in to view this page.")
        st.page_link("app.py", label="Go to Login", icon="🔐")
        st.stop()
