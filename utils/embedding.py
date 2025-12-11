
from typing import Dict
from sentence_transformers import SentenceTransformer

EMBEDDING_MODELS: Dict[str, str] = {
    "mini": "all-MiniLM-L6-v2",
    "mpnet": "all-mpnet-base-v2",
}

_model_cache: Dict[str, SentenceTransformer] = {}


def get_text_model(key: str = "mini") -> SentenceTransformer:
    if key not in EMBEDDING_MODELS:
        raise ValueError(f"Unknown model '{key}'. Use: {list(EMBEDDING_MODELS.keys())}")

    if key not in _model_cache:
        _model_cache[key] = SentenceTransformer(EMBEDDING_MODELS[key])

    return _model_cache[key]


def embed(text: str, model_key: str = "mini"):
    model = get_text_model(model_key)
    vector = model.encode(text)
    return vector.tolist()

