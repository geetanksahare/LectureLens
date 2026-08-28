"""
LectureLens - Central Configuration
---------------------------------------------------------
Single source of truth for API keys, model names, and shared
paths used across the entire backend.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------
# API KEYS
# ---------------------------------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. Make sure you have a .env file "
        "in the project root with:\n"
        "GROQ_API_KEY=your_key_here"
    )

# ---------------------------------------------------------
# BACKBLAZE B2 SETTINGS
# ---------------------------------------------------------
B2_KEY_ID = os.environ.get("B2_KEY_ID")
B2_APPLICATION_KEY = os.environ.get("B2_APPLICATION_KEY")
B2_BUCKET_NAME = os.environ.get("B2_BUCKET_NAME")
B2_ENDPOINT_URL = os.environ.get("B2_ENDPOINT_URL")

# ---------------------------------------------------------
# LLM MODEL
# ---------------------------------------------------------
MODEL_NAME = "openai/gpt-oss-20b"

# ---------------------------------------------------------
# WHISPER SETTINGS
# ---------------------------------------------------------
WHISPER_MODEL_SIZE = "base"
WHISPER_DEVICE = "cuda"
WHISPER_COMPUTE_TYPE = "float16"

# ---------------------------------------------------------
# OUTPUT PATHS
# ---------------------------------------------------------
TRANSCRIPTS_DIR = "outputs/transcripts"
SUBTITLES_DIR = "outputs/subtitles"
GLOSSARY_PATH = "outputs/glossary.json"
QUIZ_DIR = "outputs/quizzes"

# ---------------------------------------------------------
# CHUNKING SETTINGS
# ---------------------------------------------------------
# Bumped from 500 -> 1200: fewer chunks = less repeated prompt
# overhead and far fewer total API calls for long lectures.
CHUNK_MAX_WORDS = 1000

# ---------------------------------------------------------
# QUIZ SETTINGS
# ---------------------------------------------------------
MCQS_PER_CHUNK = 3
SHORT_ANSWERS_PER_CHUNK = 1

# ---------------------------------------------------------
# COMBINED-CALL TOKEN BUDGETS
# ---------------------------------------------------------
# One LLM call per chunk now returns technical summary + simple
# summary + glossary (+ quiz, when requested) as a single JSON
# blob, so this needs headroom for all of it at once.
MAX_TOKENS_COMBINED_NO_QUIZ = 700
MAX_TOKENS_COMBINED_WITH_QUIZ = 1200


# ---------------------------------------------------------
# CUSTOM EXCEPTIONS
# ---------------------------------------------------------
class DailyQuotaExceeded(Exception):
    """Raised when Groq's tokens-per-day limit is hit.
    Retrying with backoff can never succeed within the retry
    window for this error, so callers should fail fast instead."""
    pass