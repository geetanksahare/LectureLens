"""
models.py
---------------------------------------------------------
SQL schema definitions for LectureLens.

Tables:
  users               - registered accounts
  lecture_history     - one row per processed lecture
  transcript_segments - one row per Whisper segment (keeps timestamps)
  quiz_results        - one row per quiz attempt
"""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

CREATE_LECTURE_HISTORY_TABLE = """
CREATE TABLE IF NOT EXISTS lecture_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    full_transcript TEXT,
    technical_summary TEXT,
    simple_summary TEXT,
    srt_path TEXT,
    vtt_path TEXT,
    processed_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users (id)
);
"""

CREATE_TRANSCRIPT_SEGMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS transcript_segments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER NOT NULL,
    segment_index INTEGER NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY (lecture_id) REFERENCES lecture_history (id)
);
"""

CREATE_QUIZ_RESULTS_TABLE = """
CREATE TABLE IF NOT EXISTS quiz_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lecture_id INTEGER NOT NULL,
    score INTEGER NOT NULL,
    total_questions INTEGER NOT NULL,
    taken_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (lecture_id) REFERENCES lecture_history (id)
);
"""

ALL_TABLES = [
    CREATE_USERS_TABLE,
    CREATE_LECTURE_HISTORY_TABLE,
    CREATE_TRANSCRIPT_SEGMENTS_TABLE,
    CREATE_QUIZ_RESULTS_TABLE,
]