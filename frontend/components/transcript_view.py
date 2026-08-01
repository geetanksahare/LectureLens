"""
transcript_view.py
---------------------------------------------------------
Reusable component that renders a timestamped transcript.
Used by both the Process Lecture page (right after processing)
and the History page (when reopening a past lecture).
"""

import streamlit as st


def format_mmss(seconds: float) -> str:
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes:02d}:{secs:02d}"


def render_transcript(segments):
    """
    segments: list of dicts with "start" (or "start_time") and "text" keys.
    Works with both:
      - transcriber.py output:      {"start": ..., "end": ..., "text": ...}
      - db_manager segment rows:    {"start_time": ..., "end_time": ..., "text": ...}
    """
    for seg in segments:
        start = seg.get("start", seg.get("start_time"))
        text = seg.get("text", "")
        st.markdown(f"`[{format_mmss(start)}]` {text}")
