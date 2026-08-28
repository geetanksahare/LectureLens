from summarization.summarizer import process_transcript, flatten_glossary


def run_summary(segments, include_quiz=False):
    processed = process_transcript(segments, include_quiz=include_quiz)
    glossary = flatten_glossary(processed)
    return processed, glossary