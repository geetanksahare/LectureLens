"""
LectureLens - Transcriber Module
---------------------------------------------------------
Takes a lecture audio/video file and produces a timestamped
transcript using faster-whisper (local, free, no API needed).

Output format (used by every other module in the pipeline):
[
    {"start": 0.0, "end": 3.5, "text": "Welcome to today's lecture..."},
    {"start": 3.5, "end": 7.2, "text": "Let's start with the base case"},
    ...
]

Requires: pip install faster-whisper
"""
import time
import os
import json
from faster_whisper import WhisperModel
from utils.config import (
    WHISPER_MODEL_SIZE,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    TRANSCRIPTS_DIR,
)


# ---------------------------------------------------------
# 1. MODEL LOADING
# ---------------------------------------------------------
def load_model(model_size=WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=WHISPER_COMPUTE_TYPE):
    print(f"Loading Whisper model: {model_size} ({device}, {compute_type})...")
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    return model


# ---------------------------------------------------------
# 2. TRANSCRIPTION
# ---------------------------------------------------------
def transcribe_audio(file_path, model=None, model_size=WHISPER_MODEL_SIZE, language=None):
    """
    file_path: path to audio/video file (.mp3, .wav, .mp4, etc.)
    model: pass an already-loaded WhisperModel to avoid reloading each call
    language: force a language code (e.g. "en") or leave None for auto-detect

    Returns: list of segments -> [{"start": ..., "end": ..., "text": ...}]
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    if model is None:
        model = load_model(model_size)

    print(f"Transcribing: {file_path}")

    segments_generator, info = model.transcribe(
        file_path,
        language=language,
        beam_size=5,
        vad_filter=True,          # skips silent portions, faster + cleaner output
        vad_parameters=dict(min_silence_duration_ms=500),
    )

    print(f"Detected language: {info.language} (confidence: {info.language_probability:.2f})")
    print(f"Audio duration: {info.duration:.1f}s")

    segments = []
    for seg in segments_generator:
        segments.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip()
        })

    return segments


# ---------------------------------------------------------
# 3. SAVE TRANSCRIPT TO JSON (for reuse by other modules / debugging)
# ---------------------------------------------------------
def save_transcript(segments, output_path=None, filename="transcript.json"):
    if output_path is None:
        output_path = os.path.join(TRANSCRIPTS_DIR, filename)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)
    print(f"Transcript saved to {output_path}")
    return output_path


# ---------------------------------------------------------
# 4. LOAD TRANSCRIPT FROM JSON (skip re-running Whisper during dev/testing)
# ---------------------------------------------------------
def load_transcript(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# 5. FULL PIPELINE HELPER - one call, audio in, segments + saved file out
# ---------------------------------------------------------
def process_audio(file_path, output_path=None, model_size=WHISPER_MODEL_SIZE, language=None):
    model = load_model(model_size)
    segments = transcribe_audio(file_path, model=model, language=language)

    if output_path is None:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(TRANSCRIPTS_DIR, f"{base_name}.json")

    save_transcript(segments, output_path)
    return segments


# ---------------------------------------------------------
# 6. EXAMPLE USAGE
# ---------------------------------------------------------
if __name__ == "__main__":
    # Replace with a real lecture audio file path for testing
    sample_file = "data/audio/sample_lecture.mp3"

    segments = process_audio(sample_file)

    print(f"\nGenerated {len(segments)} segments\n")
    for seg in segments[:5]:
        print(f"[{seg['start']}s -> {seg['end']}s] {seg['text']}")
        
def process_audio_chunked(file_path, work_dir, model_size=WHISPER_MODEL_SIZE, language=None, segment_seconds=600):
    """
    Splits long audio into fixed-length segments before transcribing,
    to avoid memory allocation failures on long lecture recordings.
    Merges segment results into one continuous, correctly-timestamped
    list of segments.
    """
    from audio_extraction.audio_extractor import split_audio

    split_dir = os.path.join(work_dir, "audio_segments")
    audio_segments = split_audio(file_path, split_dir, segment_seconds=segment_seconds)

    if not audio_segments:
        # Fallback: file too short to split meaningfully, transcribe directly
        return process_audio(file_path)

    model = load_model(model_size)
    all_segments = []

    for segment_path, offset in audio_segments:
        print(f"Transcribing segment starting at {offset}s...")
        segs = transcribe_audio(segment_path, model=model, language=language)
        for seg in segs:
            seg["start"] += offset
            seg["end"] += offset
        all_segments.extend(segs)

    return all_segments