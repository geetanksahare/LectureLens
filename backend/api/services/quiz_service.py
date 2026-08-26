from summarization.summarizer import chunk_transcript
from quiz_generation.quiz_generator import generate_quiz


def run_quiz(segments):
    chunks = chunk_transcript(segments)
    return generate_quiz(chunks)