from summarization.summarizer import chunk_transcript
from api.services.embedding_service import embed_texts
from api.supabase_client import supabase


def generate_and_store_embeddings(lecture_id: str, segments: list):
    """
    Chunks the transcript, generates embeddings for each chunk,
    and stores them in the transcript_embeddings table for later
    retrieval by the RAG chatbot.
    """
    chunks = chunk_transcript(segments)

    if not chunks:
        return

    chunk_texts = [c["text"] for c in chunks]
    embeddings = embed_texts(chunk_texts)

    rows = []
    for chunk, embedding in zip(chunks, embeddings):
        rows.append({
            "lecture_id": lecture_id,
            "chunk_text": chunk["text"],
            "chunk_start": chunk["start"],
            "chunk_end": chunk["end"],
            "embedding": embedding,
        })

    supabase.table("transcript_embeddings").insert(rows).execute()
    
from utils.config import GROQ_API_KEY, MODEL_NAME
from utils import prompts
from groq import Groq, RateLimitError
from api.services.embedding_service import embed_text
import time

client = Groq(api_key=GROQ_API_KEY, timeout=30.0)

SIMILARITY_THRESHOLD = 0.35  # tune this based on testing


def call_llm(prompt, temperature=0.3, max_tokens=400, max_retries=5):
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            print(f"[rag_service] Rate limit hit, retrying in {wait_time}s...")
            time.sleep(wait_time)


def answer_question(lecture_id: str, question: str):
    """
    Answers a question about a lecture using RAG. Returns a dict with
    the answer, its source ("lecture" or "general_knowledge"), and
    supporting timestamps if grounded.
    """
    question_embedding = embed_text(question)

    result = supabase.rpc("match_transcript_chunks", {
        "query_embedding": question_embedding,
        "match_lecture_id": lecture_id,
        "match_count": 3,
    }).execute()

    matches = result.data or []

    best_similarity = matches[0]["similarity"] if matches else 0.0

    print(f"[RAG DEBUG] Question: '{question}' | Best similarity: {best_similarity:.4f} | Threshold: {SIMILARITY_THRESHOLD}")
    if matches:
        print(f"[RAG DEBUG] Top match chunk_start={matches[0]['chunk_start']}, text preview: {matches[0]['chunk_text'][:150]}...")

    if best_similarity >= SIMILARITY_THRESHOLD:
        context_chunks = [m["chunk_text"] for m in matches]
        prompt = prompts.grounded_answer_prompt(question, context_chunks)
        answer = call_llm(prompt)

        if answer.strip() == "NOT_COVERED":
            general_answer = call_llm(prompts.general_knowledge_answer_prompt(question))
            return {
                "answer": general_answer,
                "source": "general_knowledge",
                "timestamps": [],
            }

        timestamps = [{"start": m["chunk_start"], "end": m["chunk_end"]} for m in matches]
        return {
            "answer": answer,
            "source": "lecture",
            "timestamps": timestamps,
        }
    else:
        general_answer = call_llm(prompts.general_knowledge_answer_prompt(question))
        return {
            "answer": general_answer,
            "source": "general_knowledge",
            "timestamps": [],
        }