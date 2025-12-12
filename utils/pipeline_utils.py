# utils/pipeline_utils.py

import json
from typing import List, Any

from typing import List, Any

def combine_chunks(
    baseline_chunks: List[Any],
    embedding_chunks: List[Any],
    ) -> List[Any]:


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
