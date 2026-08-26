from audio_extraction.audio_extractor import extract_audio


def run_audio_extraction(video_path: str, audio_output_path: str):
    success, message, duration = extract_audio(video_path, audio_output_path)
    if not success:
        raise RuntimeError(f"Audio extraction failed: {message}")
    return audio_output_path, duration