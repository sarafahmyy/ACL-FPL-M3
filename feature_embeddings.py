from kg_retrieval import run_cypher 
from intent_entity import ParsedInput
from utils.embedding import embed


# ---------- SEMANTIC SEARCH OVER FEATURE EMBEDDINGS ----------

def semantic_player_search(
    parsed: ParsedInput,
    model_key: str = "text-embedding-3-large",
    k: int = 5,
):
    """
    Integrated semantic search that:
      - Uses the same ParsedInput from intent_entity.extract_entities
      - Embeds the user's *raw* question text
      - Searches over player FEATURE embeddings
      - Optionally filters by position (GK/DEF/MID/FWD) if the LLM found it

    This makes the semantic search part of the same pipeline as the baseline.
    """

    # 1) Use the original user text as the semantic description
    description = parsed.raw

    query_vec = embed(description, model_key=model_key)

    # 3) Choose the correct index
    index_name = f"player_feature_embedding_2{model_key.replace('-', '_')}"

    # 4) Extract any useful constraints from entities
    position = parsed.entities.position  # "FWD", "MID", "DEF", "GK" or None

    # 5) Vector search + optional position filter in Cypher
    cypher = """
    CALL db.index.vector.queryNodes($index_name, $k, $embedding)
    YIELD node, score
    OPTIONAL MATCH (node)-[:PLAYS_AS]->(pos:Position)
    WHERE $position IS NULL OR pos.name = $position
    RETURN
        node.player_name AS player,
        pos.name AS position,
        score
    ORDER BY score DESC
    """

    params = {
        "index_name": index_name,
        "k": k,
        "embedding": query_vec,
        "position": position,
    }

    rows = run_cypher(cypher, params)

    # --- Remove duplicate players by name (keep first occurrence) ---
    seen = set()
    unique_rows = []


    for row in rows:
        name = row["player"]
        row["confidence"] = row.pop("score")
        if name in seen:
            continue
        seen.add(name)
        unique_rows.append(row)

    return {
        "intent": parsed.intent,
        "entities": parsed.entities,
        "model_key": model_key,
        "rows": unique_rows,
    }


# ---------- DEMO BLOCK (OPTIONAL FOR LOCAL TESTING) ----------

if __name__ == "__main__":
    from intent_entity import extract_entities

    queries = [
        "fast attacking forward who scores many goals",
        "creative midfielder with many assists",
        "goalkeeper with many saves and clean sheets",
    ]

    for model_key in ["text-embedding-3-small", "text-embedding-3-large"]:

        print(f"\n=== SEMANTIC SEARCH USING {model_key.upper()} ===")
        for q in queries:
            print(f"\nQuery: {q}")
            parsed = extract_entities(q)
            results = semantic_player_search(parsed, model_key=model_key, k=5)

            for row in results["rows"]:
                print(f"  {row['player']} ({row['position']})  score={row['score']:.3f}")
