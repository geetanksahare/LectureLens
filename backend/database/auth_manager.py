"""
auth_manager.py
---------------------------------------------------------
Handles user signup and login for LectureLens.
Passwords are hashed with bcrypt - never stored in plain text.

Requires: pip install bcrypt
"""

import re
import bcrypt
from backend.database.db_manager import create_user, get_user_by_username


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _check_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _is_valid_email(email: str) -> bool:
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email) is not None


def signup(username: str, email: str, password: str, confirm_password: str):
    """
    Returns (success: bool, message: str)
    """
    username = username.strip()
    email = email.strip()

    if not username or not email or not password:
        return False, "All fields are required."

    if len(username) < 3:
        return False, "Username must be at least 3 characters."

    if not _is_valid_email(email):
        return False, "Please enter a valid email address."

    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    if password != confirm_password:
        return False, "Passwords do not match."

    if get_user_by_username(username) is not None:
        return False, "That username is already taken."

    password_hash = _hash_password(password)
    create_user(username, email, password_hash)

    return True, "Account created successfully. You can now log in."


def login(username: str, password: str):
    """
    Returns (success: bool, message: str, user: dict | None)
    """
    username = username.strip()

    user = get_user_by_username(username)
    if user is None:
        return False, "Username not found.", None

    if not _check_password(password, user["password_hash"]):
        return False, "Incorrect password.", None

    return True, "Login successful.", user