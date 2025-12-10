from typing import Dict, Any, List

from input_embedding import embed_user_text
from kg_retrieval import get_driver, run_cypher 
from intent_entity import ParsedInput


# ---------- 2.b.1 FETCH AGGREGATED PLAYER FEATURES FROM NEO4J ----------

def fetch_player_feature_rows() -> List[Dict[str, Any]]:
    """
    returns one Python dict per player containing all relevant stats.

    Returns rows like:
    {
        "player_name": "Erling Haaland",
        "seasons": ["2022-23"],
        "position": "FWD",
        "matches": 35,
        "minutes": 2800,
        "goals_scored": 36,
        "assists": 8,
        "total_points": 272,
        "bonus": 40,
        "clean_sheets": 5,
        "goals_conceded": 20,
        "own_goals": 0,
        "penalties_saved": 0,
        "penalties_missed": 1,
        "yellow_cards": 3,
        "red_cards": 0,
        "saves": 0,
        "bps": 380,
        "avg_influence": 40.2,
        "avg_creativity": 25.7,
        "avg_threat": 60.3,
        "avg_ict_index": 12.1,
        "avg_form": 6.4
    }
    """

    query = """
    MATCH (p:Player)-[r:PLAYED_IN]->(f:Fixture)
          <-[:HAS_FIXTURE]-(gw:Gameweek)
          <-[:HAS_GW]-(s:Season)
    OPTIONAL MATCH (p)-[:PLAYS_AS]->(pos:Position)

    WITH
        p,
        collect(DISTINCT s.season_name) AS seasons,
        head(collect(DISTINCT pos.name)) AS position,

        count(DISTINCT f) AS matches,

        // DIRECT NUMERIC COUNTS / SUMS
        sum(COALESCE(r.minutes, 0))                AS minutes,
        sum(COALESCE(r.goals_scored, 0))           AS goals_scored,
        sum(COALESCE(r.assists, 0))                AS assists,
        sum(COALESCE(r.total_points, 0))           AS total_points,
        sum(COALESCE(r.bonus, 0))                  AS bonus,
        sum(COALESCE(r.clean_sheets, 0))           AS clean_sheets,
        sum(COALESCE(r.goals_conceded, 0))         AS goals_conceded,
        sum(COALESCE(r.own_goals, 0))              AS own_goals,
        sum(COALESCE(r.penalties_saved, 0))        AS penalties_saved,
        sum(COALESCE(r.penalties_missed, 0))       AS penalties_missed,
        sum(COALESCE(r.yellow_cards, 0))           AS yellow_cards,
        sum(COALESCE(r.red_cards, 0))              AS red_cards,
        sum(COALESCE(r.saves, 0))                  AS saves,
        sum(COALESCE(r.bps, 0))                    AS bps,

        // ADVANCED METRICS AS AVERAGES PER MATCH
        avg(COALESCE(r.influence, 0.0))            AS avg_influence,
        avg(COALESCE(r.creativity, 0.0))           AS avg_creativity,
        avg(COALESCE(r.threat, 0.0))               AS avg_threat,
        avg(COALESCE(r.ict_index, 0.0))            AS avg_ict_index,
        avg(COALESCE(r.form, 0.0))                 AS avg_form

    RETURN
        p.player_name AS player_name,
        seasons,
        position,
        matches,
        minutes,
        goals_scored,
        assists,
        total_points,
        bonus,
        clean_sheets,
        goals_conceded,
        own_goals,
        penalties_saved,
        penalties_missed,
        yellow_cards,
        red_cards,
        saves,
        bps,
        avg_influence,
        avg_creativity,
        avg_threat,
        avg_ict_index,
        avg_form
    ORDER BY player_name
    """

    rows = run_cypher(query)
    return rows


# ---------- 2.b.2 BUILD TEXT DESCRIPTION FROM THESE FEATURES ----------

def build_feature_description(row: Dict[str, Any]) -> str:
    """
    Convert row into a text description for the embedding model
    """

    player = row.get("player_name", "Unknown player")
    seasons = row.get("seasons", [])
    season_text = ", ".join(seasons) if seasons else "unknown seasons"

    position = row.get("position") or "Unknown position"
    matches = row.get("matches", 0) or 0

    minutes = row.get("minutes", 0) or 0
    goals_scored = row.get("goals_scored", 0) or 0
    assists = row.get("assists", 0) or 0
    total_points = row.get("total_points", 0) or 0
    bonus = row.get("bonus", 0) or 0
    clean_sheets = row.get("clean_sheets", 0) or 0
    goals_conceded = row.get("goals_conceded", 0) or 0
    own_goals = row.get("own_goals", 0) or 0
    penalties_saved = row.get("penalties_saved", 0) or 0
    penalties_missed = row.get("penalties_missed", 0) or 0
    yellow_cards = row.get("yellow_cards", 0) or 0
    red_cards = row.get("red_cards", 0) or 0
    saves = row.get("saves", 0) or 0
    bps = row.get("bps", 0) or 0

    avg_influence = row.get("avg_influence", 0.0) or 0.0
    avg_creativity = row.get("avg_creativity", 0.0) or 0.0
    avg_threat = row.get("avg_threat", 0.0) or 0.0
    avg_ict_index = row.get("avg_ict_index", 0.0) or 0.0
    avg_form = row.get("avg_form", 0.0) or 0.0

    desc = (
        f"Player: {player}. "
        f"Seasons: {season_text}. "
        f"Position: {position}. "
        f"Matches played: {matches}. "
        f"Minutes played: {minutes}. "
        f"Goals scored: {goals_scored}. "
        f"Assists: {assists}. "
        f"Total FPL points: {total_points}. "
        f"Bonus points: {bonus}. "
        f"Clean sheets: {clean_sheets}. "
        f"Goals conceded: {goals_conceded}. "
        f"Own goals: {own_goals}. "
        f"Penalties saved: {penalties_saved}. "
        f"Penalties missed: {penalties_missed}. "
        f"Yellow cards: {yellow_cards}. "
        f"Red cards: {red_cards}. "
        f"Saves: {saves}. "
        f"BPS total: {bps}. "
        f"Average influence: {avg_influence:.2f}. "
        f"Average creativity: {avg_creativity:.2f}. "
        f"Average threat: {avg_threat:.2f}. "
        f"Average ICT index: {avg_ict_index:.2f}. "
        f"Average form: {avg_form:.2f}."
    )

    return desc


# ---------- 2.b.3 CREATE VECTOR INDEX FOR FEATURE EMBEDDINGS ----------

def ensure_feature_embedding_index(model_key: str, dim: int) -> None:
    """
    Create a Neo4j vector index for the feature embeddings for a given model.

    Index name:   player_feature_embedding_<model_key>
    Property:     feature_embedding_<model_key>
    """

    index_name = f"player_feature_embedding_{model_key}"
    prop_name = f"feature_embedding_{model_key}"

    cypher = f"""
    CREATE VECTOR INDEX {index_name} IF NOT EXISTS
    FOR (p:Player) ON (p.{prop_name})
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: $dim,
        `vector.similarity_function`: 'cosine'
      }}
    }}
    """

    run_cypher(cypher, {"dim": dim})


# ---------- 2.b.4 STORE FEATURE EMBEDDINGS ON PLAYER NODES ----------

def store_feature_embeddings(
    rows: List[Dict[str, Any]],
    embeddings: List[List[float]],
    model_key: str,
) -> None:
    """
    Store one feature embedding per Player node.

    Property name will be:
        p.feature_embedding_<model_key>
    """

    if not rows:
        return
    if len(rows) != len(embeddings):
        raise ValueError("rows and embeddings must have the same length.")

    prop_name = f"feature_embedding_{model_key}"

    driver = get_driver()
    query_template = f"""
    MATCH (p:Player {{player_name: $player_name}})
    SET p.{prop_name} = $embedding
    """

    with driver.session() as session:
        for row, vec in zip(rows, embeddings):
            session.run(query_template, {
                "player_name": row["player_name"],
                "embedding": vec,
            })


# ---------- 2.b.5 FULL PIPELINE: BUILD FEATURE EMBEDDINGS PER MODEL ----------

def build_feature_embeddings_for_players(model_key: str = "mini") -> int:
    """
    Full pipeline for one embedding model ("mini" or "mpnet"):

    1. Fetch aggregated player features using the exact PLAYED_IN fields.
    2. Build text descriptions from these features.
    3. Embed them using the chosen model.
    4. Create / ensure the vector index.
    5. Store embeddings on Player nodes.

    Returns: number of players processed.
    """

    rows = fetch_player_feature_rows()
    if not rows:
        print("No player rows found in KG.")
        return 0

    descriptions = [build_feature_description(row) for row in rows]

    embeddings: List[List[float]] = []
    for desc in descriptions:
        vec = embed_user_text(desc, model_key=model_key)
        embeddings.append(vec)

    dim = len(embeddings[0])
    ensure_feature_embedding_index(model_key=model_key, dim=dim)
    store_feature_embeddings(rows, embeddings, model_key=model_key)

    print(f"[{model_key}] Stored feature embeddings for {len(rows)} players.")
    return len(rows)


# ---------- 2.b.6 SEMANTIC SEARCH OVER FEATURE EMBEDDINGS ----------

def search_players_by_features(
    description: str,
    model_key: str = "mini",
    k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Semantic search over players based on their FEATURE embeddings.

    Example queries:
      - "explosive forward with many goals and few yellow cards"
      - "creative midfielder with high assists and strong form"
      - "goalkeeper with many saves and clean sheets"
    """

    query_vec = embed_user_text(description, model_key=model_key)

    index_name = f"player_feature_embedding_{model_key}"

    cypher = """
    CALL db.index.vector.queryNodes($index_name, $k, $embedding)
    YIELD node, score
    RETURN
        node.player_name AS player,
        score
    ORDER BY score DESC
    """

    params = {
        "index_name": index_name,
        "k": k,
        "embedding": query_vec,
    }

    rows = run_cypher(cypher, params)
    return rows


def semantic_player_search(
    parsed: ParsedInput,
    model_key: str = "mini",
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

    # 2) Embed the question using the chosen model (mini or mpnet)
    query_vec = embed_user_text(description, model_key=model_key)

    # 3) Choose the correct index
    index_name = f"player_feature_embedding_{model_key}"

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

    for model_key in ["mini", "mpnet"]:
        print("\n" + "#" * 60)
        print(f"BUILDING FEATURE EMBEDDINGS FOR MODEL: {model_key}")
        print("#" * 60)

        build_feature_embeddings_for_players(model_key=model_key)

        print(f"\n=== SEMANTIC SEARCH USING {model_key.upper()} ===")
        for q in queries:
            print(f"\nQuery: {q}")
            parsed = extract_entities(q)
            results = semantic_player_search(parsed, model_key=model_key, k=5)

            for row in results["rows"]:
                print(f"  {row['player']} ({row['position']})  score={row['score']:.3f}")
