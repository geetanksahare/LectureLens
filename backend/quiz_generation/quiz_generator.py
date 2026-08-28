"""
LectureLens - Quiz Generator Module
---------------------------------------------------------
build_quiz_output() extracts the quiz portion from a process_transcript()
result that was run with include_quiz=True (shared LLM call with
summary/glossary — no extra API calls needed).

generate_quiz() is a standalone fallback: computes summary+quiz together
via process_transcript() when no shared 'processed' result is available.
"""

import os
import json
import time
from groq import Groq, RateLimitError
from utils.config import (
    GROQ_API_KEY,
    MODEL_NAME,
    QUIZ_DIR,
    MCQS_PER_CHUNK,
    SHORT_ANSWERS_PER_CHUNK,
)
from utils import prompts

client = Groq(api_key=GROQ_API_KEY, timeout=30.0)
MODEL = MODEL_NAME


def call_llm(prompt, temperature=0.2, max_tokens=150, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = response.choices[0].message.content.strip()
            if not content:
                if attempt == max_retries - 1:
                    raise RuntimeError("Model returned an empty response after all retries.")
                print(f"[quiz_generator] Empty response received, retrying (attempt {attempt + 1}/{max_retries})...")
                time.sleep(2)
                continue
            return content
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            print(f"[quiz_generator] Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait_time)


def build_quiz_output(processed: dict) -> dict:
    """
    Extracts the {"quiz": [...]} shape from a process_transcript()
    result that included quiz_sections (include_quiz=True).
    """
    quiz_sections = processed.get("quiz_sections", [])
    return {"quiz": quiz_sections}


def generate_quiz(chunks_or_segments, mcqs_per_chunk=MCQS_PER_CHUNK, short_answers_per_chunk=SHORT_ANSWERS_PER_CHUNK):
    """
    Standalone fallback path: computes summary+glossary+quiz together
    (one LLM call per chunk) purely to obtain the quiz, when no shared
    'processed' result was already computed by run_summary().
    """
    from summarization.summarizer import process_transcript

    # Accept either raw segments or pre-chunked chunks for flexibility
    if chunks_or_segments and "text" in chunks_or_segments[0] and "start" in chunks_or_segments[0] and "end" in chunks_or_segments[0] and "original" not in chunks_or_segments[0]:
        # looks like raw segments (has "text","start","end" but not "original")
        segments = chunks_or_segments
    else:
        segments = chunks_or_segments

    processed = process_transcript(segments, include_quiz=True, mcqs_per_chunk=mcqs_per_chunk, short_answers_per_chunk=short_answers_per_chunk)
    return build_quiz_output(processed)


def grade_short_answer(question, model_answer, student_answer):
    prompt = prompts.grading_prompt(question, model_answer, student_answer)
    raw = call_llm(prompt, temperature=0.2, max_tokens=150)
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"correct": False, "feedback": "Could not evaluate answer automatically."}

    return result


def get_weak_areas(quiz_results, student_answers):
    weak_areas = []

    for section in quiz_results["quiz"]:
        for q in section["mcqs"]:
            student_choice = student_answers.get(q["question"])
            if student_choice is not None and student_choice != q["correct_option"]:
                weak_areas.append({
                    "question": q["question"],
                    "your_answer": student_choice,
                    "correct_answer": q["correct_option"],
                    "timestamp": q["timestamp"],
                    "explanation": q.get("explanation", "")
                })

    return weak_areas


def save_quiz(quiz_result, output_dir=QUIZ_DIR, filename="quiz.json"):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(quiz_result, f, indent=2, ensure_ascii=False)

    print(f"Quiz saved to {output_path}")
    return output_path