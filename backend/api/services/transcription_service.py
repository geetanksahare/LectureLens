from transcription.transcriber import process_audio


def run_transcription(audio_path: str, output_json_path: str):
    segments = process_audio(audio_path, output_path=output_json_path)
    return segments