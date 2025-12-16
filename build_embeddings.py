from typing import Any, Dict, List
from kg_retrieval import run_cypher
from utils.embedding import embed
from typing import Dict

from utils.neo4j_connection import get_driver

import ast

def load_embeddings(model_key: str):
    with open(f"feature_embeddings_{model_key}.txt", "r", encoding="utf-8") as f:
        embeddings_str = f.read()
    
    # Convert the string back to a list of embeddings
    embeddings = ast.literal_eval(embeddings_str)
    
    return embeddings

# Load the embeddings from the file

# You can now use `embeddings` directly in your function or process further


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

def build_feature_description(row: Dict[str, Any]) -> str:
    """
    Convert row into a text description for the embedding model
    """

    player = row.get("player_name", "Unknown player")
    seasons = row.get("seasons", [])
    season_text = ", ".join(seasons) if seasons else "unknown seasons"

    position = row.get("position") or "Unknown position"
    
    goals_scored = row.get("goals_scored", 0) or 0
    assists = row.get("assists", 0) or 0
    total_points = row.get("total_points", 0) or 0
    
    clean_sheets = row.get("clean_sheets", 0) or 0
    avg_form = row.get("avg_form", 0.0) or 0.0

    desc = (
        f"Player: {player}. "
        f"Seasons: {season_text}. "
        f"Position: {position}. "
        f"Goals scored: {goals_scored}. "
        f"Assists: {assists}. "
        f"Total FPL points: {total_points}. "
        f"Clean sheets: {clean_sheets}. "
        f"Average form: {avg_form:.2f}."
    )

    return desc
def ensure_feature_embedding_index(model_key: str, dim: int = 1536) -> None:
    """
    Create a Neo4j vector index for the feature embeddings for a given model.
    """
    # Replace hyphen with underscore in the model key to avoid syntax issues in Cypher
    index_name = f"player_feature_embedding_2{model_key.replace('-', '_')}"
    prop_name = f"feature_embedding_2{model_key.replace('-', '_')}"

    # Quote the index name to handle any special characters like hyphens
    cypher = f"""
    CREATE VECTOR INDEX `{index_name}` IF NOT EXISTS
    FOR (p:Player) ON (p.{prop_name})
    OPTIONS {{
      indexConfig: {{
        `vector.dimensions`: $dim,
        `vector.similarity_function`: 'cosine'
      }}
    }}
    """

    # Run the Cypher query
    run_cypher(cypher, {"dim": dim})

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

    # Replace hyphens with underscores in the property name for valid Cypher syntax
    prop_name = f"feature_embedding_2{model_key.replace('-', '_')}"

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

def build_feature_embeddings_for_players(model_key: str = "text-embedding-3-large") -> int:
    """
    Full pipeline for one embedding model ("text-embedding-3-large" or "text-embedding-3-small"):

    1. Fetch aggregated player features using the exact PLAYED_IN fields.
    2. Build text descriptions from these features.
    3. Embed them using the chosen OpenAI model.
    4. Create / ensure the vector index.
    5. Store embeddings on Player nodes.

    Returns: number of players processed.
    """
    rows = fetch_player_feature_rows()
    if not rows:
        print("No player rows found in KG.")
        return 0

    descriptions = [build_feature_description(row) for row in rows]
    i=0
    embeddings: List[List[float]] = []
    for desc in descriptions:
        
        print(desc,"\n")
        vec = embed(desc, model_key=model_key)  # Use OpenAI's embedding model here

        embeddings.append(vec)
        print(f"Embedded player {i+1}/{len(descriptions)}")
        i+=1
        


        



    dim = len(embeddings[0])
    ensure_feature_embedding_index(model_key=model_key, dim=dim)
    store_feature_embeddings(rows, embeddings, model_key=model_key)

    print(f"[{model_key}] Stored feature embeddings for {len(rows)} players.")
    return len(rows)

if __name__ == "__main__":
    for model_key in ["text-embedding-3-small"]:
        print("\n" + "#" * 60)
        print(f"BUILDING FEATURE EMBEDDINGS FOR MODEL: {model_key}")
        print("#" * 60)

        build_feature_embeddings_for_players(model_key=model_key)

       