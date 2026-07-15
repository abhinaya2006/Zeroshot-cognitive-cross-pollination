import math
from typing import List, Union
from app.config import settings

# Global cache for the sentence-transformers model to avoid reloading
_model = None

def get_sentence_transformer():
    global _model
    if _model is not None:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(settings.embeddings_model)
        return _model
    except Exception as e:
        print(f"Warning: Could not load sentence-transformers ({e}). Falling back to TF-IDF.")
        return None

def cosine_similarity_vec(v1: List[float], v2: List[float]) -> float:
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_a = math.sqrt(sum(a * a for a in v1))
    norm_b = math.sqrt(sum(b * b for b in v2))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)

def tfidf_similarity(text1: str, text2: str) -> float:
    """Fallback TF-IDF similarity calculation in pure Python."""
    def tokenize(text: str) -> List[str]:
        return [w.strip(".,!?\"'()[]{}").lower() for w in text.split() if w.strip()]

    tokens1 = tokenize(text1)
    tokens2 = tokenize(text2)
    
    if not tokens1 or not tokens2:
        return 0.0

    all_tokens = set(tokens1 + tokens2)
    
    # Simple term frequency
    tf1 = {t: tokens1.count(t) for t in all_tokens}
    tf2 = {t: tokens2.count(t) for t in all_tokens}
    
    # We treat all words as having IDF=1 (bag-of-words similarity)
    vec1 = [tf1[t] for t in all_tokens]
    vec2 = [tf2[t] for t in all_tokens]
    
    return cosine_similarity_vec(vec1, vec2)

def get_similarity(text1: str, text2: str) -> float:
    """
    Computes cosine similarity between two texts.
    Uses sentence-transformers if available, otherwise falls back to pure Python TF-IDF.
    """
    model = get_sentence_transformer()
    if model is not None:
        try:
            embeddings = model.encode([text1, text2])
            # encode returns numpy array. We can calculate similarity using dot product since they are normalized,
            # but let's do safe cosine calculation.
            v1, v2 = embeddings[0].tolist(), embeddings[1].tolist()
            return cosine_similarity_vec(v1, v2)
        except Exception as e:
            print(f"Embedding encoding failed ({e}). Falling back to TF-IDF.")
            return tfidf_similarity(text1, text2)
    else:
        return tfidf_similarity(text1, text2)
