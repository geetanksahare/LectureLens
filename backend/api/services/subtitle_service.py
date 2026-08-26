from subtitle_generation.subtitle_generator import save_subtitles


def run_subtitle_generation(segments, output_dir: str, filename: str):
    return save_subtitles(segments, output_dir=output_dir, filename=filename)