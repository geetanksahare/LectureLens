"""
db_manager.py
---------------------------------------------------------
Handles all SQLite connections and queries for LectureLens.
Every other module (auth, frontend pages) should go through
these functions rather than writing raw SQL directly.
"""

import sqlite3
import os
from backend.database.models import ALL_TABLES

DB_PATH = os.path.join(os.path.dirname(__file__), "lecturelens.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # lets us access columns by name
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    """Creates all tables if they don't already exist. Safe to call every app startup."""
    conn = get_connection()
    cursor = conn.cursor()
    for statement in ALL_TABLES:
        cursor.execute(statement)
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# USERS
# ---------------------------------------------------------
def create_user(username, email, password_hash):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        (username, email, password_hash),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id


def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------
# LECTURE HISTORY
# ---------------------------------------------------------
def create_lecture(user_id, filename, full_transcript, technical_summary,
                    simple_summary, srt_path=None, vtt_path=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO lecture_history
           (user_id, filename, full_transcript, technical_summary, simple_summary, srt_path, vtt_path)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, filename, full_transcript, technical_summary, simple_summary, srt_path, vtt_path),
    )
    conn.commit()
    lecture_id = cursor.lastrowid
    conn.close()
    return lecture_id


def get_lectures_for_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM lecture_history WHERE user_id = ? ORDER BY processed_at DESC",
        (user_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_lecture_by_id(lecture_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lecture_history WHERE id = ?", (lecture_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# ---------------------------------------------------------
# TRANSCRIPT SEGMENTS (timestamped)
# ---------------------------------------------------------
def add_transcript_segments(lecture_id, segments):
    """
    segments: list of {"start": ..., "end": ..., "text": ...}
    (exact format returned by transcriber.process_audio())
    """
    conn = get_connection()
    cursor = conn.cursor()
    for i, seg in enumerate(segments):
        cursor.execute(
            """INSERT INTO transcript_segments
               (lecture_id, segment_index, start_time, end_time, text)
               VALUES (?, ?, ?, ?, ?)""",
            (lecture_id, i, seg["start"], seg["end"], seg["text"]),
        )
    conn.commit()
    conn.close()


def get_transcript_segments(lecture_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM transcript_segments WHERE lecture_id = ? ORDER BY segment_index ASC",
        (lecture_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------
# QUIZ RESULTS
# ---------------------------------------------------------
def save_quiz_result(lecture_id, score, total_questions):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO quiz_results (lecture_id, score, total_questions) VALUES (?, ?, ?)",
        (lecture_id, score, total_questions),
    )
    conn.commit()
    result_id = cursor.lastrowid
    conn.close()
    return result_id


def get_quiz_results_for_lecture(lecture_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM quiz_results WHERE lecture_id = ? ORDER BY taken_at DESC",
        (lecture_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_dashboard_stats(user_id):
    """Returns simple aggregate stats for the Dashboard page."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM lecture_history WHERE user_id = ?", (user_id,))
    lecture_count = cursor.fetchone()["count"]

    cursor.execute(
        """SELECT AVG(CAST(score AS FLOAT) / total_questions * 100) as avg_score
           FROM quiz_results
           JOIN lecture_history ON quiz_results.lecture_id = lecture_history.id
           WHERE lecture_history.user_id = ?""",
        (user_id,),
    )
    row = cursor.fetchone()
    avg_score = row["avg_score"] if row and row["avg_score"] is not None else None

    conn.close()
    return {"lecture_count": lecture_count, "avg_quiz_score": avg_score}