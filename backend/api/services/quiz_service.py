from summarization.summarizer import process_transcript, chunk_transcript
from quiz_generation.quiz_generator import build_quiz_output, generate_quiz


def run_quiz(segments, processed=None):
    """
    Reuses an already-computed process_transcript(include_quiz=True)
    result when available (shared pass with summary/glossary).
    Falls back to computing it standalone if called on its own.
    """
    if processed is not None and "quiz_sections" in processed:
        return build_quiz_output(processed)

    processed = process_transcript(segments, include_quiz=True)
    return build_quiz_output(processed)