"""
Section 2.a - Baseline Graph Retrieval (FPL)

This file:
- Connects to Neo4j
- Implements baseline Cypher queries using your actual KG schema.

Implemented so far:
  Baseline Query #1 -> Top players by position in a season
  Baseline Query #2 -> Player performance in a season / gameweek
"""

import os
from typing import Dict, Any, List, Optional

from neo4j import GraphDatabase
from dotenv import load_dotenv

from intent_entity import ParsedInput, QueryEntities

# Load .env so NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD are available
load_dotenv()

# ---------- Neo4j CONNECTION ----------

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


def get_driver():
    """
    Create a Neo4j driver using environment variables.
    """
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


def run_cypher(query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Small helper to run a Cypher query and return a list of dictionaries.
    """
    if params is None:
        params = {}

    driver = get_driver()
    with driver.session() as session:
        result = session.run(query, params)
        return [record.data() for record in result]


# ---------- BASELINE QUERY #1: TOP PLAYERS BY POSITION & SEASON ----------

def baseline_top_players(parsed: ParsedInput, limit: int = 10) -> Dict[str, Any]:
    """
    Answer questions like:
      - 'Top forwards in 2022-23'
      - 'Best midfielders in 2021-22 season'

    Uses entities from preprocessing:
      parsed.entities.season   -> e.g. '2022-23'
      parsed.entities.position -> 'GK' / 'DEF' / 'MID' / 'FWD' (mapped from text)

    Uses your KG schema:
      (s:Season {season_name})
        -[:HAS_GW]->(gw:Gameweek {GW_number, season})
        -[:HAS_FIXTURE]->(f:Fixture)
      (p:Player {player_name, player_element})
      (p)-[r:PLAYED_IN {total_points, ...}]->(f)
      (p)-[:PLAYS_AS]->(pos:Position {name})
    """

    season = parsed.entities.season or "2022-23"   # default if user doesn't say
    position = parsed.entities.position            # might be None

    params = {
        "season": season,
        "position": position,
        "limit": limit,
    }

    query = """
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)
    MATCH (p:Player)-[r:PLAYED_IN]->(f)
    OPTIONAL MATCH (p)-[:PLAYS_AS]->(pos:Position)
    // filter by position if provided (pos.name)
    WHERE $position IS NULL OR pos.name = $position
    WITH p, sum(r.total_points) AS total_points
    ORDER BY total_points DESC
    LIMIT $limit
    RETURN
        p.player_name AS player,
        total_points AS points
    """

    rows = run_cypher(query, params)

    return {
        "intent": parsed.intent,
        "season": season,
        "position": position,
        "query": query,
        "params": params,
        "rows": rows,
    }


# ---------- BASELINE QUERY #2: PLAYER PERFORMANCE (SEASON / GAMEWEEK) ----------

def baseline_player_performance(parsed: ParsedInput) -> Dict[str, Any]:
    """
    Answer questions like:
      - 'How many points did Haaland get in GW 3 2022-23?'
      - 'Show me total points for Mohamed Salah in 2022-23 season'

    Expected entities:
      parsed.entities.players[0] -> player name (string, must match Player.player_name)
      parsed.entities.season     -> e.g. '2022-23'
      parsed.entities.gameweek   -> optional int (e.g. 3)

    Schema used:
      (s:Season {season_name})
        -[:HAS_GW]->(gw:Gameweek {GW_number, season})
        -[:HAS_FIXTURE]->(f:Fixture)
      (p:Player {player_name})
        -[r:PLAYED_IN {total_points, ...}]->(f)
    """

    if not parsed.entities.players:
        raise ValueError("No player name provided in entities for baseline_player_performance.")

    player_name = parsed.entities.players[0]
    season = parsed.entities.season or "2022-23"
    gw = parsed.entities.gameweek  # can be None -> full season

    params = {
        "season": season,
        "player_name": player_name,
        "gw": gw,
    }

    query = """
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(gw:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)
    MATCH (p:Player {player_name: $player_name})-[r:PLAYED_IN]->(f)
    WHERE $gw IS NULL OR gw.GW_number = $gw
    WITH p, sum(r.total_points) AS total_points
    RETURN
        p.player_name AS player,
        $season AS season,
        $gw AS gameweek,
        total_points
    """

    rows = run_cypher(query, params)

    return {
        "intent": parsed.intent,
        "player_name": player_name,
        "season": season,
        "gameweek": gw,
        "query": query,
        "params": params,
        "rows": rows,
    }


def baseline_team_performance(parsed: ParsedInput):
    if not parsed.entities.teams:
        raise ValueError("Team name missing in Query 3.")

    team = parsed.entities.teams[0]
    season = parsed.entities.season or "2022-23"

    params = {"team": team, "season": season}

    query = """
    MATCH (t:Team {name: $team})
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
    MATCH (p:Player)-[r:PLAYED_IN]->(f)
    WITH t,
         count(DISTINCT f) AS matches,
         sum(r.goals_scored) AS goals,
         sum(r.assists) AS assists,
         sum(r.total_points) AS points
    RETURN t.name AS team, matches, goals, assists, points
    """

    rows = run_cypher(query, params)
    return {"query": query, "params": params, "rows": rows}




def baseline_fixtures_by_gameweek(parsed: ParsedInput):
    season = parsed.entities.season or "2022-23"
    gw = parsed.entities.gameweek

    if gw is None:
        raise ValueError("Gameweek is required for Query 4.")

    params = {"season": season, "gw": gw}

    query = """
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(gw:Gameweek {GW_number: $gw})
          -[:HAS_FIXTURE]->(f:Fixture)
    MATCH (f)-[:HAS_HOME_TEAM]->(home:Team)
    MATCH (f)-[:HAS_AWAY_TEAM]->(away:Team)
    RETURN f.fixture_number AS fixture,
           home.name AS home_team,
           away.name AS away_team
    ORDER BY fixture
    """

    rows = run_cypher(query, params)
    return {"query": query, "params": params, "rows": rows}





def baseline_team_fixtures(parsed: ParsedInput):
    if not parsed.entities.teams:
        raise ValueError("Team missing for Query 5.")

    team = parsed.entities.teams[0]
    season = parsed.entities.season or "2022-23"

    params = {"team": team, "season": season}

    query = """
    MATCH (t:Team {name: $team})
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(gw:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
    MATCH (f)-[:HAS_HOME_TEAM]->(home:Team)
    MATCH (f)-[:HAS_AWAY_TEAM]->(away:Team)
    RETURN gw.GW_number AS gameweek,
           home.name AS home_team,
           away.name AS away_team
    ORDER BY gameweek
    """

    rows = run_cypher(query, params)
    return {"query": query, "params": params, "rows": rows}




def baseline_player_season_stats(parsed: ParsedInput):
    if not parsed.entities.players:
        raise ValueError("Player missing for Query 6.")

    player = parsed.entities.players[0]
    season = parsed.entities.season or "2022-23"

    params = {"player": player, "season": season}

    query = """
    MATCH (p:Player {player_name: $player})
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)
    MATCH (p)-[r:PLAYED_IN]->(f)
    RETURN p.player_name AS player,
           sum(r.goals_scored) AS goals,
           sum(r.assists) AS assists,
           sum(r.total_points) AS points
    """

    rows = run_cypher(query, params)
    return {"query": query, "params": params, "rows": rows}





def baseline_player_comparison(parsed: ParsedInput):
    if len(parsed.entities.players) < 2:
        raise ValueError("Need two players for Query 7.")

    p1, p2 = parsed.entities.players[:2]
    season = parsed.entities.season or "2022-23"

    params = {"p1": p1, "p2": p2, "season": season}

    query = """
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)

    MATCH (p1:Player {player_name: $p1})-[r1:PLAYED_IN]->(f)
    MATCH (p2:Player {player_name: $p2})-[r2:PLAYED_IN]->(f)

    RETURN
        p1.player_name AS player1, sum(r1.total_points) AS p1_points,
        p2.player_name AS player2, sum(r2.total_points) AS p2_points
    """

    rows = run_cypher(query, params)
    return {"query": query, "params": params, "rows": rows}




def baseline_team_best_players(parsed: ParsedInput, limit: int = 5):
    if not parsed.entities.teams:
        raise ValueError("Team missing for Query 8.")

    team = parsed.entities.teams[0]
    season = parsed.entities.season or "2022-23"

    params = {"team": team, "season": season, "limit": limit}

    query = """
    MATCH (t:Team {name: $team})
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)

    MATCH (p:Player)-[r:PLAYED_IN]->(f)
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)

    WITH p, sum(r.total_points) AS points
    ORDER BY points DESC
    LIMIT $limit
    RETURN p.player_name AS player, points
    """

    rows = run_cypher(query, params)
    return {"query": query, "params": params, "rows": rows}







def baseline_fixture_difficulty(parsed: ParsedInput):
    if not parsed.entities.teams:
        raise ValueError("Team missing for Query 9.")

    team = parsed.entities.teams[0]
    season = parsed.entities.season or "2022-23"

    params = {"team": team, "season": season}

    query = """
    MATCH (t:Team {name: $team})
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(gw:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)

    // find the opponent
    OPTIONAL MATCH (f)-[:HAS_HOME_TEAM]->(t)
    OPTIONAL MATCH (f)-[:HAS_AWAY_TEAM]->(opp:Team)
    WHERE opp IS NOT NULL

    // opponent strength = sum of points of all their players
    MATCH (opp_player:Player)-[r:PLAYED_IN]->(f)
    WHERE (f)-[:HAS_HOME_TEAM]->(opp) OR (f)-[:HAS_AWAY_TEAM]->(opp)

    WITH gw.GW_number AS GW, opp.name AS opponent, sum(r.total_points) AS strength
    RETURN GW, opponent, strength
    ORDER BY GW
    """

    rows = run_cypher(query, params)
    return {"query": query, "params": params, "rows": rows}


def baseline_recommendation_graph_only(parsed: ParsedInput, limit: int = 3):
    season = parsed.entities.season or "2022-23"

    params = {"season": season, "limit": limit}

    query = """
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)
    MATCH (p:Player)-[r:PLAYED_IN]->(f)

    WITH p, sum(r.total_points) AS points
    ORDER BY points DESC
    LIMIT $limit

    RETURN p.player_name AS recommended, points
    """

    rows = run_cypher(query, params)
    return {"query": query, "params": params, "rows": rows}



# ============================================================
#                     DEMO: RUN ALL BASELINE QUERIES
# ============================================================

if __name__ == "__main__":

    print("\n================= BASELINE QUERY #1 =================\n")
    q1_entities = QueryEntities(season="2022-23", position="FWD")
    q1_parsed = ParsedInput("top_players", q1_entities, "Top forwards 2022/23")
    print(baseline_top_players(q1_parsed, limit=5))

    print("\n================= BASELINE QUERY #2 =================\n")
    q2_entities = QueryEntities(players=["Erling Haaland"], season="2022-23", gameweek=3)
    q2_parsed = ParsedInput("player_performance", q2_entities,
                            "How many points did Haaland get in GW 3?")
    print(baseline_player_performance(q2_parsed))

    print("\n================= BASELINE QUERY #3 =================\n")
    q3_entities = QueryEntities(teams=["Arsenal"], season="2022-23")
    q3_parsed = ParsedInput("team_analysis", q3_entities, "How did Arsenal perform?")
    print(baseline_team_performance(q3_parsed))

    print("\n================= BASELINE QUERY #4 =================\n")
    q4_entities = QueryEntities(season="2022-23", gameweek=5)
    q4_parsed = ParsedInput("fixtures_by_gw", q4_entities, "Show fixtures for GW 5")
    print(baseline_fixtures_by_gameweek(q4_parsed))

    print("\n================= BASELINE QUERY #5 =================\n")
    q5_entities = QueryEntities(teams=["Liverpool"], season="2022-23")
    q5_parsed = ParsedInput("team_fixtures", q5_entities, "Liverpool fixtures 2022/23")
    print(baseline_team_fixtures(q5_parsed))

    print("\n================= BASELINE QUERY #6 =================\n")
    q6_entities = QueryEntities(players=["Mohamed Salah"], season="2022-23")
    q6_parsed = ParsedInput("player_stats", q6_entities, "Salah stats 22/23")
    print(baseline_player_season_stats(q6_parsed))

    print("\n================= BASELINE QUERY #7 =================\n")
    q7_entities = QueryEntities(players=["Erling Haaland", "Harry Kane"], season="2022-23")
    q7_parsed = ParsedInput("player_comparison", q7_entities, "Compare Haaland and Kane 22/23")
    print(baseline_player_comparison(q7_parsed))

    print("\n================= BASELINE QUERY #8 =================\n")
    q8_entities = QueryEntities(teams=["Manchester City"], season="2022-23")
    q8_parsed = ParsedInput("team_best_players", q8_entities, "Best Man City players 22/23")
    print(baseline_team_best_players(q8_parsed))

    print("\n================= BASELINE QUERY #9 =================\n")
    q9_entities = QueryEntities(teams=["Arsenal"], season="2022-23")
    q9_parsed = ParsedInput("fixture_difficulty", q9_entities, "Arsenal fixture difficulty")
    print(baseline_fixture_difficulty(q9_parsed))

    print("\n================= BASELINE QUERY #10 =================\n")
    q10_entities = QueryEntities(season="2022-23")
    q10_parsed = ParsedInput("recommendation", q10_entities, "Who to captain?")
    print(baseline_recommendation_graph_only(q10_parsed))
