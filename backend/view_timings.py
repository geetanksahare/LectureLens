"""
TEMPORARY viewer script — just reads and prints the timing log that
job_processor.py writes automatically. No upload, no auth token needed.
Delete this file once data collection is done.
"""

import json
import os
import tempfile

TIMING_LOG_PATH = os.path.join(tempfile.gettempdir(), "lecturelens_timings.json")

if not os.path.exists(TIMING_LOG_PATH):
    print("No timing data found yet. Upload and process a lecture first.")
else:
    with open(TIMING_LOG_PATH, "r") as f:
        all_timings = json.load(f)

    print(f"\n{'='*70}")
    print(f"{'lecture_id':<38} {'audio(s)':>10} {'trans(s)':>10} {'llm(s)':>10} {'total(s)':>10}")
    print(f"{'='*70}")

    for lecture_id, t in all_timings.items():
        print(f"{lecture_id:<38} "
              f"{t.get('audio_extraction_sec', '-'):>10} "
              f"{t.get('transcription_sec', '-'):>10} "
              f"{t.get('llm_generation_sec', '-'):>10} "
              f"{t.get('total_pipeline_sec', '-'):>10}")

    print(f"{'='*70}\n")
    print("Raw JSON (in case you want more detail, e.g. audio_duration_sec):")
    print(json.dumps(all_timings, indent=2))