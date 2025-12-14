"""
Section 2.a - Baseline Graph Retrieval (FPL)

"""
from typing import Dict, Any

from intent_entity import ParsedInput, QueryEntities
from utils.neo4j_connection import run_cypher



# ---------- BASELINE QUERY #1: TOP PLAYERS BY POSITION & SEASON ----------

def baseline_top_players(parsed: ParsedInput, limit: int = 10) -> Dict[str, Any]:
    """
    Answer questions like:
      - 'Top forwards in 2022-23'
      - 'Best midfielders in 2021-22 season'
      
    """

    season = parsed.entities.season or "2022-23"   # default if user doesn't say
    position = parsed.entities.position            

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
    MATCH (p)-[:PLAYS_AS]->(pos:Position)
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

    """
    Answer questions like:
      "How did Arsenal perform last season?"
      "Show me Liverpool’s total goals and points in 2022-23
    """
    
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


def baseline_top_players_by_position(parsed: ParsedInput, limit: int = 10) -> Dict[str, Any]:
    season = parsed.entities.season or "2022-23"
    position = parsed.entities.position

    if position is None:
        raise ValueError("Position is required for baseline_top_players_by_position.")

    params = {"season": season, "position": position, "limit": limit}

    query = """
    MATCH (s:Season {season_name: $season})-[:HAS_GW]->(:Gameweek)-[:HAS_FIXTURE]->(f:Fixture)
    MATCH (p:Player)-[r:PLAYED_IN]->(f)
    MATCH (p)-[:PLAYS_AS]->(:Position {name: $position})
    WITH p, sum(r.total_points) AS points
    RETURN p.player_name AS player, $position AS position, points
    ORDER BY points DESC, player
    LIMIT $limit
    """

    rows = run_cypher(query, params)
    return {"query": query, "params": params, "rows": rows}




def baseline_players_by_position_in_season(parsed: ParsedInput, limit: int = 300) -> Dict[str, Any]:
    season = parsed.entities.season or "2022-23"
    position = parsed.entities.position

    if position is None:
        raise ValueError("Position is required for baseline_players_by_position_in_season.")

    params = {"season": season, "position": position, "limit": limit}

    query = """
    MATCH (s:Season {season_name: $season})-[:HAS_GW]->(:Gameweek)-[:HAS_FIXTURE]->(f:Fixture)
    MATCH (p:Player)-[:PLAYED_IN]->(f)
    MATCH (p)-[:PLAYS_AS]->(:Position {name: $position})
    RETURN DISTINCT p.player_name AS player, $position AS position
    ORDER BY player
    LIMIT $limit
    """

    rows = run_cypher(query, params)
    return {"query": query, "params": params, "rows": rows}


def baseline_fixtures_by_gameweek(parsed: ParsedInput):

    """
    Answer questions like:
     "What are the fixtures for GW 10?"
     "Show me all matches in gameweek 5"
     "Which teams play in GW 2?"
      
    """
   
    
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



def baseline_team_players_by_position(parsed: ParsedInput, min_appearances: int = 1) -> Dict[str, Any]:
    if not parsed.entities.teams:
        raise ValueError("Team is required for baseline_team_players_by_position.")
    if parsed.entities.position is None:
        raise ValueError("Position is required for baseline_team_players_by_position.")

    team = parsed.entities.teams[0]
    position = parsed.entities.position
    season = parsed.entities.season or "2022-23"

    params = {"team": team, "position": position, "season": season, "min_apps": min_appearances}

    query = """
    MATCH (t:Team)
    WHERE toLower(t.name) = toLower($team)
    MATCH (s:Season {season_name: $season})-[:HAS_GW]->(:Gameweek)-[:HAS_FIXTURE]->(f:Fixture)
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)

    MATCH (p:Player)-[:PLAYED_IN]->(f)
    MATCH (p)-[:PLAYS_AS]->(:Position {name: $position})

    WITH p, count(DISTINCT f) AS appearances
    WHERE appearances >= $min_apps

    RETURN p.player_name AS player, $position AS position, appearances
    ORDER BY appearances DESC, player
    """

    rows = run_cypher(query, params)
    return {"query": query, "params": params, "rows": rows}


def baseline_team_fixtures(parsed: ParsedInput):

    """
    Answer questions like:
     "Show me all Man City matches in 2022-23"
     "Who does Chelsea play in GW 15?"
      
    """

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

    """
    Answer questions like:
     "Show me Salah’s stats in 2022-23"
     "Player stats for Saka"
      
    """

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

    """
    Answer questions like:
     "Compare Haaland and Kane in 2022-23"
     "Who scored more points — Salah or De Bruyne?"
     "Haaland vs Rashford comparison"
      
    """


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

    """
    Answer questions like:
     "Best Manchester City players this season"
     "Who are Arsenal's top scorers?"
     "Show me the top 5 Liverpool players"
      
    """


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

    """
    Answer questions like:
     "How hard are Arsenal’s fixtures?"
     "Show me the opponent difficulty for Chelsea"
     "Which upcoming matches for Spurs are toughest?"
      
    """
        
    if not parsed.entities.teams:
        raise ValueError("Team not available.")

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


    """
    Answer questions like:
     "Who should I captain?"
     "Who are the best FPL players overall?"
     "Recommend a player to buy"
      
    """
        
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

def baseline_player_identity(parsed: ParsedInput) -> Dict[str, Any]:
    """
    Answers questions like:
      - 'Who is Mohamed Salah?'
      - 'Who is Haaland in 2022-23?'

    """
    if not parsed.entities.players:
        raise ValueError("Player name missing for player_identity query.")

    player_name = parsed.entities.players[0]
    season = parsed.entities.season or "2022-23"

    params = {
        "player_name": player_name,
        "season": season,
    }

    query = """
    // Find the player node
    MATCH (p:Player {player_name: $player_name})

    // Optional: position
    OPTIONAL MATCH (p)-[:PLAYS_AS]->(pos:Position)

    // Optional: total points in the given season
    OPTIONAL MATCH (p)-[r:PLAYED_IN]->(f:Fixture)
    OPTIONAL MATCH (f)<-[:HAS_FIXTURE]-(gw:Gameweek)<-[:HAS_GW]-(s:Season {season_name: $season})

    WITH p, pos, sum(COALESCE(r.total_points, 0)) AS season_points
    RETURN
        p.player_name AS player,
        pos.name AS position,
        season_points AS total_points_season
    """

    rows = run_cypher(query, params)

    return {
        "intent": parsed.intent,
        "player_name": player_name,
        "season": season,
        "query": query,
        "params": params,
        "rows": rows,
    }


def baseline_team_defense(parsed: ParsedInput) -> Dict[str, Any]:
    """
    NEW QUERY 11 - Team defensive performance (clean sheets, goals conceded)

    Answers questions like:
      - "How many clean sheets did Arsenal have in 2022-23?"
      - "Show me Liverpool defensive stats in 22/23"

    Entities used:
      parsed.entities.teams[0]  -> team name, must match (t:Team {name})
      parsed.entities.season    -> e.g. '2022-23'

    Schema assumed:
      (t:Team {name})
      (s:Season {season_name})
        -[:HAS_GW]->(:Gameweek)
        -[:HAS_FIXTURE]->(f:Fixture)
      (f)-[:HAS_HOME_TEAM]->(:Team)
      (f)-[:HAS_AWAY_TEAM]->(:Team)
      (p:Player)-[r:PLAYED_IN {clean_sheets, goals_conceded, ...}]->(f)
    """
    if not parsed.entities.teams:
        raise ValueError("Team name missing in baseline_team_defense.")

    team = parsed.entities.teams[0]
    season = parsed.entities.season or "2022-23"

    params = {
        "team": team,
        "season": season,
    }

    query = """
    MATCH (t:Team {name: $team})
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)
    WHERE (f)-[:HAS_HOME_TEAM]->(t) OR (f)-[:HAS_AWAY_TEAM]->(t)
    MATCH (p:Player)-[r:PLAYED_IN]->(f)

    // we approximate team-level defense from player stats:
    WITH t, f,
         sum(r.clean_sheets)    AS cs_sum,
         sum(r.goals_conceded)  AS goals_conceded_sum

    WITH t,
         count(DISTINCT f) AS matches,
         count(CASE WHEN cs_sum > 0 THEN 1 END) AS clean_sheets,
         sum(goals_conceded_sum) AS goals_conceded

    RETURN t.name AS team, matches, clean_sheets, goals_conceded
    """

    rows = run_cypher(query, params)
    return {
        "query": query,
        "params": params,
        "rows": rows,
    }


def baseline_player_big_games(parsed: ParsedInput, min_goals: int = 2) -> Dict[str, Any]:
    """
    NEW QUERY 12 - Player 'big games' (matches with many goals)

    Answers questions like:
      - "Show me games where Haaland scored at least 2 goals in 2022-23."
      - "In which matches did Salah score 3+ goals?"

    Entities used:
      parsed.entities.players[0] -> player name
      parsed.entities.season     -> '2022-23'
    """
    if not parsed.entities.players:
        raise ValueError("Player name missing in baseline_player_big_games.")

    player = parsed.entities.players[0]
    season = parsed.entities.season or "2022-23"

    params = {
        "player": player,
        "season": season,
        "min_goals": min_goals,
    }

    query = """
    MATCH (p:Player {player_name: $player})
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(gw:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)
    MATCH (p)-[r:PLAYED_IN]->(f)

    WHERE r.goals_scored >= $min_goals

    RETURN
        p.player_name AS player,
        gw.GW_number  AS gameweek,
        f.fixture_number AS fixture,
        r.goals_scored AS goals_in_match
    ORDER BY gameweek, fixture
    """

    rows = run_cypher(query, params)
    return {
        "query": query,
        "params": params,
        "rows": rows,
    }


def baseline_gameweek_top_scorers(parsed: ParsedInput, limit: int = 5) -> Dict[str, Any]:
    
    """
    Answers questions like:
      - "Who were the top 3 players in GW 5 of 2022-23?"
      - "Show top scorers in GW 10."

    """
    season = parsed.entities.season or "2022-23"
    gw = parsed.entities.gameweek

    if gw is None:
        raise ValueError("Gameweek is required for baseline_gameweek_top_scorers.")

    params = {
        "season": season,
        "gw": gw,
        "limit": limit,
    }

    query = """
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(gw:Gameweek {GW_number: $gw})
          -[:HAS_FIXTURE]->(f:Fixture)
    MATCH (p:Player)-[r:PLAYED_IN]->(f)

    WITH p, sum(r.total_points) AS points
    ORDER BY points DESC
    LIMIT $limit

    RETURN
        p.player_name AS player,
        $gw    AS gameweek,
        points AS total_points
    """

    rows = run_cypher(query, params)
    return {
        "query": query,
        "params": params,
        "rows": rows,
    }

def baseline_player_big_games(parsed: ParsedInput, min_goals: int = 2) -> Dict[str, Any]:
    
    """
    Answers questions like:
      - "Show me games where Haaland scored at least 2 goals in 2022-23."
      - "In which matches did Salah score 3+ goals?"

    """
    if not parsed.entities.players:
        raise ValueError("Player name missing in baseline_player_big_games.")

    player = parsed.entities.players[0]
    season = parsed.entities.season or "2022-23"

    params = {
        "player": player,
        "season": season,
        "min_goals": min_goals,
    }

    query = """
    MATCH (p:Player {player_name: $player})
    MATCH (s:Season {season_name: $season})
          -[:HAS_GW]->(gw:Gameweek)
          -[:HAS_FIXTURE]->(f:Fixture)
    MATCH (p)-[r:PLAYED_IN]->(f)

    WHERE r.goals_scored >= $min_goals

    RETURN
        p.player_name AS player,
        gw.GW_number  AS gameweek,
        f.fixture_number AS fixture,
        r.goals_scored AS goals_in_match
    ORDER BY gameweek, fixture
    """

    rows = run_cypher(query, params)
    return {
        "query": query,
        "params": params,
        "rows": rows,
    }


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


    print("\n================= BASELINE QUERY #11 =================\n")
    q11_entities = QueryEntities(players=["Erling Haaland"], season="2022-23")
    q11_parsed = ParsedInput("player_identity", q11_entities, "Who is Haaland in 22/23?")
    print(baseline_player_identity(q11_parsed))


    print("\n================= BASELINE QUERY #12 =================\n")
    q12_entities = QueryEntities(teams=["Arsenal"], season="2022-23")
    q12_parsed = ParsedInput("team_defense", q12_entities, "How many clean sheets did Arsenal have?")
    print(baseline_team_defense(q12_parsed))


    print("\n================= BASELINE QUERY #13  =================\n")
    q13_entities = QueryEntities(players=["Erling Haaland"], season="2022-23")
    q13_parsed = ParsedInput("player_big_games", q13_entities,
                             "Show me games where Haaland scored at least 2 goals in 22/23")
    print(baseline_player_big_games(q13_parsed, min_goals=2))


    print("\n================= BASELINE QUERY #14=================\n")
    q14_entities = QueryEntities(season="2022-23", gameweek=5)
    q14_parsed = ParsedInput("gw_top_scorers", q14_entities,
                             "Who were the top players in GW 5 22/23?")
    print(baseline_gameweek_top_scorers(q14_parsed, limit=5))
