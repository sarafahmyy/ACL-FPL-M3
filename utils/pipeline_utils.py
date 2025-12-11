# utils/pipeline_utils.py

import json
from typing import List, Dict, Any

def combine_chunks(
    baseline_chunks: List[Dict[str, Any]],
    embedding_chunks: List[Dict[str, Any]],
):
    seen = set()
    combined = []

    for c in baseline_chunks + embedding_chunks:
        if isinstance(c, dict):
            key = json.dumps(c, sort_keys=True)   # dict -> stable string
        else:
            key = str(c)

        if key in seen:
            continue

        seen.add(key)
        combined.append(c)

    return combined
