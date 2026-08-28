from transcription.transcriber import process_audio_chunked


def run_transcription(audio_path: str, output_json_path: str, work_dir: str = None):
    import os
    if work_dir is None:
        work_dir = os.path.dirname(audio_path)

    segments = process_audio_chunked(audio_path, work_dir)

    import json
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

    return segments