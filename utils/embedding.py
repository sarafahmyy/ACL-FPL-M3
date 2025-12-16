import os
from dotenv import load_dotenv
from openai import OpenAI
from typing import Dict, List
import openai
from sentence_transformers import SentenceTransformer

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

EMBEDDING_MODELS: Dict[str, str] = {
    "text-embedding-3-small": "text-embedding-3-small",
    "text-embedding-3-large": "text-embedding-3-large",
}

_model_cache: Dict[str, SentenceTransformer] = {}


def get_text_model(key: str = "text-embedding-3-large") -> SentenceTransformer:
    if key not in EMBEDDING_MODELS:
        raise ValueError(f"Unknown model '{key}'. Use: {list(EMBEDDING_MODELS.keys())}")

    if key not in _model_cache:
        _model_cache[key] = SentenceTransformer(EMBEDDING_MODELS[key])

    return _model_cache[key]
def embed(text: str, model_key: str = "text-embedding-3-small") -> List[float]:
    """
    This function generates embeddings using OpenAI's embeddings API (post 1.0.0 update).
    
    Args:
        text (str): The text to be embedded.
        model_key (str): The OpenAI model to use ("text-embedding-3-small" or "text-embedding-3-large").
        
    Returns:
        List[float]: The embedding vector for the input text.
    """
    try:
        # Create embedding using OpenAI's new interface
        response = openai.embeddings.create(
            model=model_key,
            input=text
        )

        # Access the embeddings from the response object
        embedding = response.data[0].embedding  # Access 'data' and get the 'embedding' attribute

        return embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return []

def get_available_embedding_keys():
    return list(EMBEDDING_MODELS.keys())


