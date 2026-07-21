"""
subtitle_generator.py
-----------------------
Converts Whisper timestamped segments into standard subtitle files
(.srt and .vtt) that can be loaded into any video player, YouTube, or
your Streamlit frontend for synced subtitle display.

Expected input format (from transcriber.py):
[
    {"start": 0.0, "end": 3.5, "text": "Welcome to today's lecture on recursion"},
    {"start": 3.5, "end": 7.2, "text": "Let's start with the base case"},
    ...
]
"""

import os
from backend.utils.config import SUBTITLES_DIR


# ---------------------------------------------------------
# STEP 1: Timestamp formatting helpers
# ---------------------------------------------------------
def format_timestamp_srt(seconds):
    """
    Converts seconds (float) into SRT timestamp format:
    HH:MM:SS,mmm
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_timestamp_vtt(seconds):
    """
    Converts seconds (float) into WebVTT timestamp format:
    HH:MM:SS.mmm
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"


# ---------------------------------------------------------
# STEP 2: Generate .srt file content
# ---------------------------------------------------------
def generate_srt(segments):
    """
    Builds SRT-formatted subtitle content from segments.
    """
    srt_lines = []

    for index, seg in enumerate(segments, start=1):
        start_time = format_timestamp_srt(seg["start"])
        end_time = format_timestamp_srt(seg["end"])
        text = seg["text"].strip()

        srt_lines.append(str(index))
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(text)
        srt_lines.append("")  # blank line between entries

    return "\n".join(srt_lines)


# ---------------------------------------------------------
# STEP 3: Generate .vtt file content
# ---------------------------------------------------------
def generate_vtt(segments):
    """
    Builds WebVTT-formatted subtitle content from segments.
    """
    vtt_lines = ["WEBVTT", ""]  # required header

    for seg in segments:
        start_time = format_timestamp_vtt(seg["start"])
        end_time = format_timestamp_vtt(seg["end"])
        text = seg["text"].strip()

        vtt_lines.append(f"{start_time} --> {end_time}")
        vtt_lines.append(text)
        vtt_lines.append("")  # blank line between entries

    return "\n".join(vtt_lines)


# ---------------------------------------------------------
# STEP 4: Save subtitle files to disk
# ---------------------------------------------------------
def save_subtitles(segments, output_dir=SUBTITLES_DIR, filename="lecture"):
    """
    Generates and saves both .srt and .vtt files.

    Returns the file paths so the frontend can load/display them.
    """
    os.makedirs(output_dir, exist_ok=True)

    srt_content = generate_srt(segments)
    vtt_content = generate_vtt(segments)

    srt_path = os.path.join(output_dir, f"{filename}.srt")
    vtt_path = os.path.join(output_dir, f"{filename}.vtt")

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    with open(vtt_path, "w", encoding="utf-8") as f:
        f.write(vtt_content)

    print(f"Subtitles saved:\n - {srt_path}\n - {vtt_path}")

    return {"srt_path": srt_path, "vtt_path": vtt_path}


# ---------------------------------------------------------
# Example usage / quick test
# ---------------------------------------------------------
if __name__ == "__main__":
    sample_segments = [
        {"start": 0.0, "end": 3.5, "text": "Welcome to today's lecture on recursion."},
        {"start": 3.5, "end": 7.2, "text": "Let's start with the base case."},
        {"start": 7.2, "end": 12.0, "text": "Recursion happens when a function calls itself."},
    ]

    paths = save_subtitles(sample_segments, filename="lecture_01")
    print(paths)