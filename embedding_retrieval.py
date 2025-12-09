"""
Section 2.b - Embedding-based Retrieval (FPL)

We implement FEATURE VECTOR EMBEDDINGS for Player nodes.

Idea:
- For each Player in a given season, we build a text description using their stats.
- We embed tha  t description with a SentenceTransformer model.
- We store the embedding on the Player node.
- For a new user query, we embed the query and find the most similar players.

We support AT LEAST TWO embedding models:
- 'mini'  -> all-MiniLM-L6-v2
- 'mpnet' -> all-mpnet-base-v2
"""

from typing import Dict, Any, List
import numpy as np

from sentence_transformers import SentenceTransformer

from kg_retrieval import run_cypher
from intent_entity import ParsedInput


# ---------- MODEL REGISTRY & LOADING ----------

EMBEDDING_MODELS: Dict[str, str] = {
    "mini": "all-MiniLM-L6-v2",       # same as 1.c input embedding (if you used it there)
    "mpnet": "all-mpnet-base-v2",     # second model for comparison
}

_model_cache: Dict[str, SentenceTransformer] = {}


def get_st_model(key: str) -> SentenceTransformer:
    """
    Load a SentenceTransformer by a short key ('mini', 'mpnet').
    Cached so we don't reload each time.
    """
    if key not in EMBEDDING_MODELS:
        raise ValueError(f"Unknown model key: {key}. Use one of {list(EMBEDDING_MODELS.keys())}.")

    if key not in _model_cache:
        _model_cache[key] = SentenceTransformer(EMBEDDING_MODELS[key])

    return _model_cache[key]


# ---------- STEP 1: BUILD FEATURE DESCRIPTIONS FROM NEO4J ----------

def fetch_player_season_summaries(season: str = "2022-23") -> List[Dict[str, Any]]:
    """
    Get one row per player in a season with aggregated stats.

    Assumes KG has:
      (s:Season {season_name})
        -[:HAS_GW]->(:Gameweek)
        -[:HAS_FIXTURE]->(f:Fixture)
      (p:Player)-[r:PLAYED_IN]->(f) with stats:
        - r.goals_scored
        - r.assists
        - r.total_points
    """
    query = """
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)
    MATCH (p:Player)-[r:PLAYED_IN]->(f)
    OPTIONAL MATCH (p)-[:PLAYS_AS]->(pos:Position)
    WITH p,
         coalesce(pos.name, 'UNKNOWN')   AS position,
         sum(r.goals_scored)             AS goals,
         sum(r.assists)                  AS assists,
         sum(r.total_points)             AS points
    RETURN
        p.player_name AS player,
        position,
        goals,
        assists,
        points
    """

    params = {"season": season}
    return run_cypher(query, params)


def build_player_description(row: Dict[str, Any], season: str) -> str:
    """
    Turn one player's stats row into a natural-language description string
    that we will embed.
    """
    player = row.get("player", "UNKNOWN")
    position = row.get("position", "UNKNOWN")
    goals = row.get("goals", 0)
    assists = row.get("assists", 0)
    points = row.get("points", 0)

    desc = (
        f"Player: {player}, position: {position}, season: {season}, "
        f"total points: {points}, goals: {goals}, assists: {assists}."
    )
    return desc


# ---------- STEP 2: WRITE EMBEDDINGS BACK TO NEO4J ----------

def store_player_embeddings(
    season: str = "2022-23",
    model_key: str = "mini",
    embedding_property: str = "embedding_mini",
):
    """
    Create / update embeddings for all players in a given season.

    - Fetch per-player stats from Neo4j.
    - Build a text description per player.
    - Embed it with SentenceTransformer.
    - Store the embedding vector as a property on the Player node.

    embedding_property examples:
      'embedding_mini', 'embedding_mpnet'
    """

    model = get_st_model(model_key)
    rows = fetch_player_season_summaries(season)

    for row in rows:
        player_name = row["player"]
        description = build_player_description(row, season)
        vec = model.encode(description).tolist()  # list[float]

        query = """
        MATCH (p:Player {player_name: $player})
        SET p[$prop] = $embedding
        """
        params = {
            "player": player_name,
            "prop": embedding_property,
            "embedding": vec,
        }
        run_cypher(query, params)

    return {
        "season": season,
        "model_key": model_key,
        "embedding_property": embedding_property,
        "players_processed": len(rows),
    }


# ---------- STEP 3: SEMANTIC SEARCH OVER PLAYER EMBEDDINGS ----------

def semantic_search_players(
    user_text: str,
    season: str = "2022-23",
    model_key: str = "mini",
    embedding_property: str = "embedding_mini",
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Semantic search: given a free-text user description, find the most similar players.

    - Use the SAME model as used in store_player_embeddings (model_key, embedding_property).
    - Encode the user_text.
    - Load all player embeddings from Neo4j.
    - Compute cosine similarity in Python.
    - Return top_k players.
    """

    model = get_st_model(model_key)
    query_vec = model.encode(user_text)

    query = f"""
    MATCH (p:Player)
    WHERE p.{embedding_property} IS NOT NULL
    RETURN p.player_name AS player, p.{embedding_property} AS embedding
    """
    rows = run_cypher(query, {})

    sims = []
    q = np.array(query_vec, dtype=float)
    for row in rows:
        emb = np.array(row["embedding"], dtype=float)
        denom = (np.linalg.norm(q) * np.linalg.norm(emb))
        if denom == 0:
            score = 0.0
        else:
            score = float(np.dot(q, emb) / denom)

        sims.append({
            "player": row["player"],
            "score": score,
        })

    sims.sort(key=lambda x: x["score"], reverse=True)
    top = sims[:top_k]

    return {
        "model_key": model_key,
        "embedding_property": embedding_property,
        "season": season,
        "user_text": user_text,
        "results": top,
    }


# ---------- STEP 4: HOOK INTO YOUR PIPELINE USING ParsedInput ----------

def embedding_player_retrieval(
    parsed: ParsedInput,
    model_key: str = "mini",
    embedding_property: str = "embedding_mini",
    top_k: int = 5,
) -> Dict[str, Any]:
    """
    Wrapper that uses ParsedInput from your preprocessing.

    For now we simply use parsed.raw (the full user question) as the text
    to embed; you could refine this by building your own "semantic intent".
    """
    text = parsed.raw
    season = parsed.entities.season or "2022-23"

    return semantic_search_players(
        user_text=text,
        season=season,
        model_key=model_key,
        embedding_property=embedding_property,
        top_k=top_k,
    )


# ---------- OPTIONAL: SMALL DEMO WHEN RUN DIRECTLY ----------

if __name__ == "__main__":
    season = "2022-23"

    print("Building embeddings with 'mini' model...")
    info_mini = store_player_embeddings(
        season=season,
        model_key="mini",
        embedding_property="embedding_mini",
    )
    print(" ->", info_mini)

    print("Building embeddings with 'mpnet' model...")
    info_mpnet = store_player_embeddings(
        season=season,
        model_key="mpnet",
        embedding_property="embedding_mpnet",
    )
    print(" ->", info_mpnet)

    user_text = "attacking midfielder with a lot of goals and assists"
    print("\nSemantic search with MINI:")
    res_mini = semantic_search_players(
        user_text,
        season=season,
        model_key="mini",
        embedding_property="embedding_mini",
        top_k=5,
    )
    print(res_mini)

    print("\nSemantic search with MPNET:")
    res_mpnet = semantic_search_players(
        user_text,
        season=season,
        model_key="mpnet",
        embedding_property="embedding_mpnet",
        top_k=5,
    )
    print(res_mpnet)
