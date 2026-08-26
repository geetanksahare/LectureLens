from summarization.summarizer import process_transcript, flatten_glossary


def run_summary(segments):
    processed = process_transcript(segments)
    glossary = flatten_glossary(processed)
    return processed, glossary