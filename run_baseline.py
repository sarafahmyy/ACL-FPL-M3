# run_baseline.py

from intent_entity import extract_entities, ParsedInput
from kg_retrieval import (
    baseline_top_players,
    baseline_player_performance,
    baseline_team_performance,
    baseline_fixtures_by_gameweek,
    baseline_team_fixtures,
    baseline_player_season_stats,
    baseline_recommendation_graph_only,
    baseline_player_identity,
    baseline_team_defense,
    baseline_player_big_games,
    baseline_gameweek_top_scorers,
    baseline_player_comparison,
    baseline_team_best_players,
    baseline_fixture_difficulty,
    baseline_team_players_by_position,
    baseline_players_by_position_in_season,
    baseline_top_players_by_position,

)


def route_baseline(parsed: ParsedInput):
    """
    Decide WHICH baseline query to run based on:
      - parsed.intent        (from 1.a LLM classifier)
      - parsed.entities      (from 1.b LLM NER)

    This is the “If intent = X and entities look like Y, call query Z” brain.
    """

    intent = parsed.intent
    text = parsed.raw.lower()
    entities = parsed.entities

    # 1) Top players (by position / season OR by gameweek)
    if intent == "top_players":
        
        if entities.position is not None and any(k in text for k in ["all", "list", "show me all", "give me all"]):
          return baseline_players_by_position_in_season(parsed, limit=300)
        
        if entities.position is not None and any(k in text for k in ["top", "best", "highest", "most points"]):
          return baseline_top_players_by_position(parsed, limit=10)
        
        if entities.gameweek is not None:
          return baseline_gameweek_top_scorers(parsed, limit=5)

        return baseline_top_players(parsed)

    # 2) Player-related questions (performance / big games / season stats)
    if intent == "player_performance":
        # CASE 0: No specific player mentioned
        # e.g. "stats and goals for midfielders in 2022-23"
        if not entities.players:
            # If the user gave a position (MID, FWD, etc.), fall back to a position-based top list
            if entities.position is not None:
                return baseline_top_players(parsed)

            # Otherwise we really can't do a player_performance query
            return {
                "intent": intent,
                "message": "I need at least one player name to show individual stats.",
            }

        # CASE 1: comparing two players
        if len(entities.players) >= 2 or " vs " in text or "versus" in text or "compare" in text:
            return baseline_player_comparison(parsed)

        # CASE 2: big games / hat-tricks
        if any(
            kw in text
            for kw in ["big game", "big games", "hat trick", "hat-trick", "3 goals", "at least 2 goals"]
        ):
            return baseline_player_big_games(parsed, min_goals=2)

        # CASE 3: specific gameweek performance
        if entities.gameweek is not None:
            return baseline_player_performance(parsed)

        # CASE 4: default single-player season stats
        return baseline_player_season_stats(parsed)


    # 3) Team-level analysis
    if intent == "team_analysis":
        # If question is about defense / clean sheets, use defensive query
        if any(kw in text for kw in ["clean sheet", "clean sheets", "defence", "defense"]):
            return baseline_team_defense(parsed)

        # NEW: best players / top scorers in that team
        if any(kw in text for kw in ["best players", "top players", "top scorers", "top 5", "top five"]):
            return baseline_team_best_players(parsed)

        # Otherwise use overall team performance
        return baseline_team_performance(parsed)


    # 4) Fixture info
    if intent == "fixture_info":
        # If we have a team name
        if entities.teams:
            # NEW: difficulty questions
            if any(kw in text for kw in ["difficulty", "hard", "tough", "easy", "fixture difficulty"]):
                return baseline_fixture_difficulty(parsed)

            # Otherwise: normal fixtures list for that team
            return baseline_team_fixtures(parsed)

        # If we only have a GW -> show all fixtures in that GW
        if entities.gameweek is not None:
            return baseline_fixtures_by_gameweek(parsed)

        # Nothing usable
        return {
            "intent": intent,
            "error": "Need a team or a gameweek to answer fixture questions."
        }

    # 5) Player identity (“Who is Mohamed Salah?”)
    if intent == "player_identity":
        return baseline_player_identity(parsed)
    
    

    # 6) Recommendation (“Who should I captain?”, “Who to buy?”)
    if intent == "recommendation":
        # Baseline: pure graph recommendation (top scorers)
        return baseline_recommendation_graph_only(parsed)

    # 7) Greetings – don’t query Neo4j, just answer politely
    if intent == "greetings":
        return {
            "intent": intent,
            "message": "Hi! Ask me about FPL players, teams, fixtures, or recommendations",
        }
        
    if intent == "team_players_by_position":
        return baseline_team_players_by_position(parsed)


    # 8) Generic or unsupported questions
    return {
        "intent": intent,
        "message": "I don't have a baseline graph query for this type of question yet.",
    }


if __name__ == "__main__":
    print("FPL Baseline Graph Assistant (type 'quit' to exit)\n")

    while True:
        user_q = input("You: ")
        if user_q.strip().lower() in ("quit", "exit"):
            break

        # 1) Preprocessing: intent + entities (and embeddings, which we ignore here)
        parsed = extract_entities(user_q)

        print("\n--- PREPROCESSING ---")
        print("Intent:", parsed.intent)
        print("Entities:", parsed.entities)

        # 2) Route to the right baseline query
        try:
            result = route_baseline(parsed)
        except Exception as e:
            print("\n[ERROR RUNNING QUERY]", e)
            print()
            continue

        # 3) Show results from Neo4j
        print("\n--- BASELINE RESULT ---")
        # greetings / unsupported
        if "rows" not in result:
            print(result.get("message", result))
        else:
            print("Query params:", result.get("params"))
            rows = result.get("rows", [])
            if not rows:
                print("No rows returned.")
            else:
                print("First few rows:")
                for row in rows[:5]:
                    print("  ", row)

        print("\n" + "=" * 80 + "\n")
