"""
LectureLens - Centralized Prompts
---------------------------------------------------------
All LLM prompt templates used across the project live here.
Keeping them in one place makes tuning faster and gives a
single reference point for the project report.

Each prompt is a function that takes the required inputs
and returns the final formatted prompt string.
"""

# ---------------------------------------------------------
# SUMMARIZATION PROMPTS (used by summarizer.py)
# ---------------------------------------------------------

def technical_summary_prompt(chunk_text):
    return f"""You are summarizing a lecture transcript for a student's study notes.

ORIGINAL TRANSCRIPT SEGMENT:
{chunk_text}

TASK:
- Summarize the key points in 3-5 sentences
- Keep the original technical terminology and formulas intact
- Do not simplify or explain jargon here — this is the technical version
- Do not add information that isn't in the transcript

TECHNICAL SUMMARY:"""


def simple_summary_prompt(chunk_text):
    return f"""You are an expert teacher explaining a lecture to a first-year student
with no prior background in this subject.

ORIGINAL TRANSCRIPT SEGMENT:
{chunk_text}

YOUR TASK:
1. Rewrite this in simple, plain English — avoid jargon
2. Use one short real-life analogy if it helps understanding
3. Keep it under 120 words
4. Do not skip any core concept, just make it easier to understand

SIMPLIFIED VERSION:"""


def glossary_extraction_prompt(chunk_text):
    return f"""Identify technical or domain-specific terms in this lecture segment
that a first-year student might not know.

TRANSCRIPT SEGMENT:
{chunk_text}

Return ONLY a JSON array, no extra text, in this exact format:
[{{"term": "...", "definition": "one-line simple definition"}}]

If there are no technical terms, return an empty array [].
"""


# ---------------------------------------------------------
# QUIZ PROMPTS (used by quiz_generator.py)
# ---------------------------------------------------------

def mcq_generation_prompt(chunk_text, num_questions):
    return f"""You are a teacher creating a short quiz based on a lecture segment.

LECTURE SEGMENT:
{chunk_text}

TASK:
Generate exactly {num_questions} multiple-choice questions that test understanding
of the concepts explained in this segment.

Rules:
- Each question must have exactly 4 options (A, B, C, D)
- Only one option should be correct
- Questions should test understanding, not just word matching
- Do not invent facts not present in the segment
- Keep each question concise

Return ONLY a JSON array, no extra text, in this exact format:
[
  {{
    "question": "...",
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct_option": "A",
    "explanation": "one-line reason why this is correct"
  }}
]
"""


def short_answer_generation_prompt(chunk_text, num_questions):
    return f"""You are a teacher creating short-answer questions based on a lecture segment.

LECTURE SEGMENT:
{chunk_text}

TASK:
Generate exactly {num_questions} short-answer questions (1-2 sentence answers expected)
that test conceptual understanding of this segment.

Return ONLY a JSON array, no extra text, in this exact format:
[
  {{
    "question": "...",
    "model_answer": "a concise correct answer (1-2 sentences)"
  }}
]
"""


def grading_prompt(question, model_answer, student_answer):
    return f"""You are grading a student's answer to a quiz question.

QUESTION: {question}
MODEL ANSWER: {model_answer}
STUDENT ANSWER: {student_answer}

TASK:
Judge if the student's answer captures the key idea of the model answer,
even if worded differently.

Return ONLY JSON in this format:
{{"correct": true or false, "feedback": "one short sentence of feedback"}}
"""