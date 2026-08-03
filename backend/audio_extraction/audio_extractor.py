"""
audio_extractor.py
---------------------------------------------------------
Extracts a clean, mono, 16kHz WAV audio track from any uploaded
video or audio file using FFmpeg.

This is the first stage of the LectureLens pipeline — Whisper
(transcription.transcriber) depends on receiving audio in this
exact format.
"""

import os
import subprocess


def extract_audio(input_path: str, output_path: str):
    """
    Extracts a mono, 16kHz WAV audio track from the given input file.

    Returns:
        (success: bool, message: str, duration_seconds: float | None)
    """
    command = [
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        output_path,
    ]

    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        return False, "FFmpeg is not installed or not found on this system's PATH.", None

    if result.returncode != 0:
        error_line = result.stderr.strip().splitlines()[-1] if result.stderr else "Unknown FFmpeg error."
        return False, error_line, None

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        return False, "FFmpeg ran but no audio file was produced.", None

    duration = get_audio_duration(output_path)
    return True, "Audio extracted successfully.", duration


def get_audio_duration(path: str):
    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        path,
    ]
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except (ValueError, FileNotFoundError):
        return None