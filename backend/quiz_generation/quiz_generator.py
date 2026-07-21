"""
LectureLens - Quiz Generator Module
---------------------------------------------------------
Takes transcript chunks (from summarizer.py) and generates
topic-wise MCQ + short-answer quiz questions with timestamps,
so wrong answers can later be linked back to the exact moment
in the lecture (weak-area detector feature).

Requires: pip install groq python-dotenv
Get a free API key from https://console.groq.com
"""

import os
import json
from groq import Groq
from backend.utils.config import (
    GROQ_API_KEY,
    MODEL_NAME,
    QUIZ_DIR,
    MCQS_PER_CHUNK,
    SHORT_ANSWERS_PER_CHUNK,
)
from backend.utils import prompts

client = Groq(api_key=GROQ_API_KEY)
MODEL = MODEL_NAME


# ---------------------------------------------------------
# 1. CORE LLM CALL
# ---------------------------------------------------------
def call_llm(prompt, temperature=0.5, max_tokens=800):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------
# 2. MCQ GENERATION FOR ONE CHUNK
# ---------------------------------------------------------
def generate_mcqs(chunk_text, start_time, num_questions=MCQS_PER_CHUNK):
    prompt = prompts.mcq_generation_prompt(chunk_text, num_questions)
    raw = call_llm(prompt, temperature=0.4, max_tokens=900)
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        questions = json.loads(raw)
    except json.JSONDecodeError:
        questions = []

    for q in questions:
        q["timestamp"] = round(start_time, 1)
        q["type"] = "mcq"

    return questions


# ---------------------------------------------------------
# 3. SHORT-ANSWER QUESTION GENERATION FOR ONE CHUNK
# ---------------------------------------------------------
def generate_short_answer(chunk_text, start_time, num_questions=SHORT_ANSWERS_PER_CHUNK):
    prompt = prompts.short_answer_generation_prompt(chunk_text, num_questions)
    raw = call_llm(prompt, temperature=0.4, max_tokens=600)
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        questions = json.loads(raw)
    except json.JSONDecodeError:
        questions = []

    for q in questions:
        q["timestamp"] = round(start_time, 1)
        q["type"] = "short_answer"

    return questions


# ---------------------------------------------------------
# 4. GRADING A SHORT-ANSWER RESPONSE (optional, LLM-as-grader)
# ---------------------------------------------------------
def grade_short_answer(question, model_answer, student_answer):
    prompt = prompts.grading_prompt(question, model_answer, student_answer)
    raw = call_llm(prompt, temperature=0.2, max_tokens=150)
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"correct": False, "feedback": "Could not evaluate answer automatically."}

    return result


# ---------------------------------------------------------
# 5. FULL QUIZ PIPELINE - runs across all transcript chunks
# ---------------------------------------------------------
def generate_quiz(chunks, mcqs_per_chunk=MCQS_PER_CHUNK, short_answers_per_chunk=SHORT_ANSWERS_PER_CHUNK):
    """
    chunks: list of dicts like {"start": ..., "end": ..., "text": "..."}
            (same format produced by chunk_transcript() in summarizer.py)
    """
    quiz_sections = []

    for i, chunk in enumerate(chunks):
        print(f"Generating quiz for chunk {i+1}/{len(chunks)}...")

        mcqs = generate_mcqs(chunk["text"], chunk["start"], mcqs_per_chunk)
        short_answers = generate_short_answer(chunk["text"], chunk["start"], short_answers_per_chunk)

        quiz_sections.append({
            "chunk_start": chunk["start"],
            "chunk_end": chunk["end"],
            "mcqs": mcqs,
            "short_answers": short_answers
        })

    return {"quiz": quiz_sections}


# ---------------------------------------------------------
# 6. WEAK AREA DETECTOR - maps wrong answers back to timestamps
# ---------------------------------------------------------
def get_weak_areas(quiz_results, student_answers):
    """
    student_answers: dict mapping question text -> student's chosen option
                      e.g. {"What is the time complexity...": "B"}
    """
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


# ---------------------------------------------------------
# 7. SAVE QUIZ TO JSON (for Streamlit UI / export)
# ---------------------------------------------------------
def save_quiz(quiz_result, output_dir=QUIZ_DIR, filename="quiz.json"):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(quiz_result, f, indent=2, ensure_ascii=False)

    print(f"Quiz saved to {output_path}")
    return output_path


# ---------------------------------------------------------
# 8. EXAMPLE USAGE
# ---------------------------------------------------------
if __name__ == "__main__":
    sample_chunks = [
        {
            "start": 0.0,
            "end": 30.0,
            "text": "Today we will study Dijkstra's algorithm, which is a greedy "
                    "approach used to find the shortest path in a weighted graph. "
                    "It uses a priority queue to always expand the least-cost node first. "
                    "The time complexity using a min-heap is O((V+E) log V)."
        }
    ]

    quiz_result = generate_quiz(sample_chunks, mcqs_per_chunk=2, short_answers_per_chunk=1)
    print(json.dumps(quiz_result, indent=2))

    save_quiz(quiz_result, filename="sample_quiz.json")

    if quiz_result["quiz"][0]["mcqs"]:
        first_q = quiz_result["quiz"][0]["mcqs"][0]["question"]
        fake_answers = {first_q: "D"}
        weak = get_weak_areas(quiz_result, fake_answers)
        print("\nWeak areas detected:")
        print(json.dumps(weak, indent=2))