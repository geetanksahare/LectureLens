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

def grounded_answer_prompt(question, context_chunks):
    context = "\n\n".join(context_chunks)
    return f"""You are answering a student's question using ONLY the lecture transcript excerpts below.

TRANSCRIPT EXCERPTS:
{context}

QUESTION: {question}

RULES:
- Answer using ONLY information contained in the excerpts above
- Do NOT use any outside knowledge
- If the excerpts do not contain enough information to answer, respond exactly with: "NOT_COVERED"
- Keep the answer concise and directly address the question

ANSWER:"""


def general_knowledge_answer_prompt(question):
    return f"""Answer the following question using your general knowledge, but be honest about uncertainty.

QUESTION: {question}

RULES:
- If this asks about specific, niche, or private details of a real product/company/website (e.g. internal pricing mechanics, specific payment processors used, undocumented features) that you do not have reliable, verifiable knowledge of, say so plainly instead of guessing or inventing plausible-sounding details.
- Only state something as fact if you are actually confident it is true and well-established.
- It's better to say "I don't have reliable information about this specific detail" than to produce a plausible-sounding guess.
- Keep the answer concise.

ANSWER:"""

# ---------------------------------------------------------
# COMBINED PROMPT (used by summarizer.py's process_chunk_combined)
# ---------------------------------------------------------
def combined_chunk_prompt(chunk_text, include_quiz=True, num_mcqs=3, num_short=1):
    quiz_instructions = ""
    quiz_fields = ""

    if include_quiz:
        quiz_instructions = f"""
5. Generate exactly {num_mcqs} multiple-choice questions (4 options A-D, exactly one correct) that test understanding of this segment
6. Generate exactly {num_short} short-answer question(s) (1-2 sentence expected answer) that test conceptual understanding"""
        quiz_fields = f''',
  "mcqs": [
    {{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct_option": "A", "explanation": "one-line reason"}}
  ],
  "short_answers": [
    {{"question": "...", "model_answer": "a concise correct answer (1-2 sentences)"}}
  ]'''

    return f"""You are analyzing a lecture transcript segment for a student's study material. Do ALL of the following in one response:

1. Write a technical summary (3-5 sentences, keep original terminology and formulas intact, no simplification)
2. Write a simplified version for a first-year student with no background (plain English, one short analogy if it helps, under 120 words)
3. Extract technical/jargon terms a first-year student might not know, each with a one-line definition (empty array if none)
4. Do not invent information that isn't present in the transcript segment{quiz_instructions}

TRANSCRIPT SEGMENT:
{chunk_text}

Return ONLY valid JSON, no markdown fences, no preamble, no text outside the JSON, in this exact shape:
{{
  "technical_summary": "...",
  "simple_summary": "...",
  "glossary": [{{"term": "...", "definition": "..."}}]{quiz_fields}
}}
"""

def combined_processing_prompt(chunk_text, include_quiz=False, num_mcqs=3, num_short_answers=1):
    quiz_instructions = ""
    quiz_schema = ""

    if include_quiz:
        quiz_instructions = f"""
4. "mcqs": exactly {num_mcqs} multiple-choice questions, each with 4 options (A-D), one correct answer, and a one-line explanation. Test understanding, not just word matching. Do not invent facts not present in the segment.
5. "short_answers": exactly {num_short_answers} short-answer questions (1-2 sentence expected answers) testing conceptual understanding, each with a concise model answer."""
        quiz_schema = """,
  "mcqs": [
    {"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "correct_option": "A", "explanation": "..."}
  ],
  "short_answers": [
    {"question": "...", "model_answer": "..."}
  ]"""

    return f"""You are creating study materials from a lecture transcript segment.

TRANSCRIPT SEGMENT:
{chunk_text}

Produce the following and return them as a single valid JSON object, with no extra text before or after:

1. "technical_summary": a 3-5 sentence summary keeping original technical terminology intact
2. "simple_summary": a plain-English explanation under 120 words, using one analogy if helpful, for a first-year student with no background
3. "glossary": a JSON array of technical/jargon terms from this segment a first-year student might not know, each as {{"term": "...", "definition": "one-line simple definition"}}. Use an empty array if there are none.{quiz_instructions}

Return ONLY this JSON object:
{{"technical_summary": "...", "simple_summary": "...", "glossary": [...]{quiz_schema}}}
"""