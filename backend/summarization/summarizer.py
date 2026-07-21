"""
LectureLens - Transcript Summarizer / Simplifier Module
---------------------------------------------------------
Takes a Whisper transcript (list of timestamped segments) and produces:
  1. Chunked transcript (grouped into ~500 token blocks, keeping timestamps)
  2. Technical summary (concise, keeps original terminology)
  3. Simplified "ELI-Junior" version (plain English, analogies, no jargon)

Requires: pip install groq --break-system-packages
Get a free API key from https://console.groq.com
"""

import os
import json
from groq import Groq

# ---------------------------------------------------------
# 1. SETUP
# ---------------------------------------------------------
# Set your key as an environment variable: export GROQ_API_KEY="your_key_here"
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = "llama-3.3-70b-versatile"  # free-tier model on Groq


# ---------------------------------------------------------
# 2. CHUNKING - group Whisper segments into ~500-word blocks
# ---------------------------------------------------------
def chunk_transcript(segments, max_words=500):
    """
    segments: list of dicts like {"start": 12.4, "end": 18.1, "text": "..."}
    Returns: list of chunks, each with start_time, end_time, and combined text
    """
    chunks = []
    current_words = 0
    current_text = []
    chunk_start = None

    for seg in segments:
        if chunk_start is None:
            chunk_start = seg["start"]

        current_text.append(seg["text"].strip())
        current_words += len(seg["text"].split())

        if current_words >= max_words:
            chunks.append({
                "start": chunk_start,
                "end": seg["end"],
                "text": " ".join(current_text)
            })
            current_text = []
            current_words = 0
            chunk_start = None

    # leftover
    if current_text:
        chunks.append({
            "start": chunk_start,
            "end": segments[-1]["end"],
            "text": " ".join(current_text)
        })

    return chunks


# ---------------------------------------------------------
# 3. CORE LLM CALL
# ---------------------------------------------------------
def call_llm(prompt, temperature=0.4, max_tokens=600):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------
# 4. TECHNICAL SUMMARY (keeps original terminology, just condensed)
# ---------------------------------------------------------
def summarize_technical(chunk_text):
    prompt = f"""You are summarizing a lecture transcript for a student's study notes.

ORIGINAL TRANSCRIPT SEGMENT:
{chunk_text}

TASK:
- Summarize the key points in 3-5 sentences
- Keep the original technical terminology and formulas intact
- Do not simplify or explain jargon here — this is the technical version
- Do not add information that isn't in the transcript

TECHNICAL SUMMARY:"""
    return call_llm(prompt)


# ---------------------------------------------------------
# 5. SIMPLIFIED "ELI-JUNIOR" VERSION
# ---------------------------------------------------------
def simplify_eli_junior(chunk_text):
    prompt = f"""You are an expert teacher explaining a lecture to a first-year student
with no prior background in this subject.

ORIGINAL TRANSCRIPT SEGMENT:
{chunk_text}

YOUR TASK:
1. Rewrite this in simple, plain English — avoid jargon
2. Use one short real-life analogy if it helps understanding
3. Keep it under 120 words
4. Do not skip any core concept, just make it easier to understand

SIMPLIFIED VERSION:"""
    return call_llm(prompt, temperature=0.6)


# ---------------------------------------------------------
# 6. GLOSSARY EXTRACTION (bonus - jargon + definitions + timestamp)
# ---------------------------------------------------------
def extract_glossary(chunk_text, start_time):
    prompt = f"""Identify technical or domain-specific terms in this lecture segment
that a first-year student might not know.

TRANSCRIPT SEGMENT:
{chunk_text}

Return ONLY a JSON array, no extra text, in this exact format:
[{{"term": "...", "definition": "one-line simple definition"}}]

If there are no technical terms, return an empty array [].
"""
    raw = call_llm(prompt, temperature=0.2, max_tokens=400)

    # Clean up in case the model wraps it in markdown fences
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        terms = json.loads(raw)
    except json.JSONDecodeError:
        terms = []

    for t in terms:
        t["timestamp"] = round(start_time, 1)

    return terms


# ---------------------------------------------------------
# 7. FULL PIPELINE - runs on all chunks
# ---------------------------------------------------------
def process_transcript(segments):
    """
    Takes raw Whisper segments and returns a structured result:
    {
        "chunks": [
            {
                "start": ..., "end": ...,
                "original": "...",
                "technical_summary": "...",
                "simple_summary": "...",
                "glossary": [...]
            },
            ...
        ]
    }
    """
    chunks = chunk_transcript(segments)
    results = []

    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")

        technical = summarize_technical(chunk["text"])
        simple = simplify_eli_junior(chunk["text"])
        glossary = extract_glossary(chunk["text"], chunk["start"])

        results.append({
            "start": chunk["start"],
            "end": chunk["end"],
            "original": chunk["text"],
            "technical_summary": technical,
            "simple_summary": simple,
            "glossary": glossary
        })

    return {"chunks": results}


# ---------------------------------------------------------
# 8. EXAMPLE USAGE
# ---------------------------------------------------------
if __name__ == "__main__":
    # Example: this would normally come from your Whisper output
    sample_segments = [
        {"start": 0.0, "end": 15.0,
         "text": "Today we will study Dijkstra's algorithm, which is a greedy "
                 "approach used to find the shortest path in a weighted graph. "
                 "It uses a priority queue to always expand the least-cost node first."},
        {"start": 15.0, "end": 30.0,
         "text": "The time complexity of this algorithm using a min-heap is "
                 "O((V+E) log V), where V is the number of vertices and E is the "
                 "number of edges in the graph."},
    ]

    output = process_transcript(sample_segments)
    print(json.dumps(output, indent=2))