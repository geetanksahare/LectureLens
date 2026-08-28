from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    """
    Lazily loads the embedding model once and reuses it across calls,
    avoiding a slow reload on every single request.
    """
    global _model
    if _model is None:
        print("Loading embedding model: all-MiniLM-L6-v2...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_text(text: str) -> list[float]:
    """
    Converts a single piece of text into a 384-dimensional embedding vector.
    """
    model = get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Converts a batch of texts into embeddings in one call — more efficient
    than calling embed_text() in a loop for multiple chunks.
    """
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()