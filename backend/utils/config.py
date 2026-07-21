"""
LectureLens - Central Configuration
---------------------------------------------------------
Single source of truth for API keys, model names, and shared
paths used across the entire backend.

Every module should import from here instead of loading
os.environ / hardcoding values individually.
"""

import os
from dotenv import load_dotenv

# ---------------------------------------------------------
# Load environment variables from .env file
# ---------------------------------------------------------
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
# LLM MODEL (used by summarizer.py and quiz_generator.py)
# ---------------------------------------------------------
MODEL_NAME = "llama-3.3-70b-versatile"

# ---------------------------------------------------------
# WHISPER SETTINGS (used by transcriber.py)
# ---------------------------------------------------------
WHISPER_MODEL_SIZE = "base"      # options: tiny, base, small, medium, large-v3
WHISPER_DEVICE = "cpu"
WHISPER_COMPUTE_TYPE = "int8"

# ---------------------------------------------------------
# OUTPUT PATHS (used across transcriber.py, subtitle_generator.py, summarizer.py)
# ---------------------------------------------------------
TRANSCRIPTS_DIR = "outputs/transcripts"
SUBTITLES_DIR = "outputs/subtitles"
GLOSSARY_PATH = "outputs/glossary.json"
QUIZ_DIR = "outputs/quizzes"

# ---------------------------------------------------------
# CHUNKING SETTINGS (used by summarizer.py's chunk_transcript())
# ---------------------------------------------------------
CHUNK_MAX_WORDS = 500

# ---------------------------------------------------------
# QUIZ SETTINGS (used by quiz_generator.py's generate_quiz())
# ---------------------------------------------------------
MCQS_PER_CHUNK = 3
SHORT_ANSWERS_PER_CHUNK = 1