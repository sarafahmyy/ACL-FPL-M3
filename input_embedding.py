# input_embedding.py

from typing import Dict
from sentence_transformers import SentenceTransformer

from utils.embedding import embed


if __name__ == "__main__":
    user_text = "attacking midfielder with lots of goals and assists"
    vec = embed(user_text, model_key="mini")
    print("Vector length:", len(vec))
    print("First 20 values:", vec[:20])
