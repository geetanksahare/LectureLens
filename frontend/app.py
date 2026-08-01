"""
LectureLens - Main Entry Point (Login / Signup)
---------------------------------------------------------
This is the landing page shown when the app starts.
Logged-out users see Login/Signup tabs here.
Logged-in users are redirected to the Dashboard.

Run from the project root:
    streamlit run frontend/app.py
"""

import os
import sys

import streamlit as st

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database.db_manager import init_db
from backend.auth.auth_manager import signup, login

# Make sure DB tables exist on every app startup
init_db()

st.set_page_config(page_title="LectureLens", page_icon="🎓", layout="centered")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# If already logged in, skip straight to the Dashboard
if st.session_state["logged_in"]:
    st.switch_page("pages/1_Dashboard.py")

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
            st.success(message)
            st.switch_page("pages/1_Dashboard.py")
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


