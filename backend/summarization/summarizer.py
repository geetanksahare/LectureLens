"""
LectureLens - Transcript Summarizer / Simplifier Module
---------------------------------------------------------
Takes a Whisper transcript (list of timestamped segments) and produces:
  1. Chunked transcript (grouped into ~500 word blocks, keeping timestamps)
  2. Technical summary (concise, keeps original terminology)
  3. Simplified "ELI-Junior" version (plain English, analogies, no jargon)
  4. Glossary of jargon terms (per-chunk, plus a clean deduplicated flat list)

Requires: pip install groq python-dotenv
Get a free API key from https://console.groq.com
"""

import json
from groq import Groq
from backend.utils.config import GROQ_API_KEY, MODEL_NAME

# ---------------------------------------------------------
# 1. SETUP
# ---------------------------------------------------------
client = Groq(api_key=GROQ_API_KEY)
MODEL = MODEL_NAME


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
# 6. GLOSSARY EXTRACTION (jargon + definitions + timestamp, per chunk)
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
# 8. FLATTEN + DEDUPE GLOSSARY (clean final glossary for display/export)
# ---------------------------------------------------------
def flatten_glossary(processed_result):
    """
    Takes the output of process_transcript() and returns one clean,
    deduplicated glossary list sorted by when the term first appeared.

    Input:  {"chunks": [{"glossary": [...]}, {"glossary": [...]}, ...]}
    Output: [
        {"term": "recursion", "definition": "...", "timestamp": 12.5},
        {"term": "base case", "definition": "...", "timestamp": 45.0},
        ...
    ]
    """
    seen_terms = set()
    flat_glossary = []

    for chunk in processed_result["chunks"]:
        for term in chunk["glossary"]:
            term_key = term.get("term", "").lower().strip()

            if not term_key or term_key in seen_terms:
                continue

            seen_terms.add(term_key)
            flat_glossary.append(term)

    return sorted(flat_glossary, key=lambda t: t["timestamp"])


# ---------------------------------------------------------
# 9. SAVE FLATTENED GLOSSARY TO JSON (for Streamlit UI / export)
# ---------------------------------------------------------
def save_glossary(flat_glossary, output_path="outputs/glossary.json"):
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(flat_glossary, f, indent=2, ensure_ascii=False)
    print(f"Glossary saved to {output_path}")
    return output_path


# ---------------------------------------------------------
# 10. EXAMPLE USAGE
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

    clean_glossary = flatten_glossary(output)
    save_glossary(clean_glossary)

    print("\nFinal deduplicated glossary:")
    for entry in clean_glossary:
        print(f"[{entry['timestamp']}s] {entry['term']}: {entry['definition']}")
