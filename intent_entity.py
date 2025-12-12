from dataclasses import dataclass, field
from typing import List, Optional
import os
import json
from huggingface_hub import InferenceClient

from utils.embedding import embed


# ---------- DATA STRUCTURES ----------

@dataclass
class QueryEntities:
    """
    Holds all FPL-related entities we can extract from the user input.
    """
    players: List[str] = field(default_factory=list)
    teams: List[str] = field(default_factory=list)
    season: Optional[str] = None
    gameweek: Optional[int] = None
    position: Optional[str] = None   # GK, DEF, MID, FWD
    stats: List[str] = field(default_factory=list)  # e.g. ["total_points", "goals_scored"]


@dataclass
class ParsedInput:
    """
    Final result of preprocessing: intent + entities + raw text.
    """
    intent: str
    entities: QueryEntities
    raw: str


# ---------- 1.a INTENT CLASSIFICATION ----------

INTENT_LABELS = [
    "recommendation",
    "player_performance",
    "top_players",
    "fixture_info",
    "team_analysis",
    "player_identity",
    "generic_question",
    "greetings",
]

VALID_SEASONS = ["2021-22", "2022-23"]



def _get_hf_client() -> InferenceClient:
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN environment variable not set!")
    return InferenceClient(
        model="google/gemma-2-2b-it",
        token=hf_token,
    )


def classify_intent(user_input: str) -> str:
    """
    Uses the LLM (Gemma 2B IT) to classify the user's intent.
    """
    client = _get_hf_client()

    prompt = f"""
You are an intent classifier for a Fantasy Premier League (FPL) assistant.

Your job is to classify user questions into EXACTLY ONE of these categories:

- recommendation
- player_performance
- top_players
- fixture_info
- team_analysis
- player_identity
- generic_question
- greetings

Return ONLY the label. No explanations.



=====================
FEW-SHOT EXAMPLES
=====================

User: "Who should I captain this week?"
Intent: recommendation

User: "How many points did Mohamed Salah score in GW 4?"
Intent: player_performance

User: "Top defenders in the 2023 season"
Intent: top_players

User: "What is Arsenal's next fixture?"
Intent: fixture_info

User: "How did Manchester United perform last season?"
Intent: team_analysis

User: "Who is Mohamed Salah?"
Intent: player_identity

User: "Tell me something interesting about FPL"
Intent: generic_question

User: "Hi"
Intent: greetings

=====================
CLASSIFY THIS QUESTION
=====================

User: "{user_input}"
Intent:
"""

    response = client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=10,
    )

    raw = response["choices"][0]["message"]["content"].strip().lower()

    # clean matching
    for label in INTENT_LABELS:
        if label in raw:
            return label

    return "generic_question"


# ---------- 1.b ENTITY EXTRACTION  ----------

def llm_extract_entities(user_input: str) -> dict:
    """
    Uses Gemma 2B IT to extract structured entities from the text (NER-style),
    with NO regex/keyword rules. All logic is in the LLM prompt.

    It should:
    - detect players, teams, season, gameweek, position, stats
    - correct obvious typos (e.g. "halaand" -> "Erling Haaland")
    - map stats to FPL property names
    """
    client = _get_hf_client()

    prompt = f"""
You are an information extraction system for Fantasy Premier League (FPL).

Read the text and extract FPL-related entities.
Return ONLY valid JSON with these fields:

{{
  "players": [],   // list of player full names as strings
  "teams": [],     // list of team names as strings
  "season": null,  // string like "2022-23" or null
  "gameweek": null,// integer gameweek number or null
  "position_filter": null, // one of "GK", "DEF", "MID", "FWD" or null
  "stats": []      // list of property names like:
                  // "total_points", "goals_scored", "assists",
                  // "minutes", "yellow_cards", "red_cards", "clean_sheets"
}}


CRITICAL:
- Extract ONLY what is explicitly stated in TEXT.
- Do NOT use football knowledge.
- The field "position" MUST be null unless the TEXT explicitly contains one of these words:
  goalkeeper, gk, defender(s), defence/defense, midfielder(s), forward(s), striker(s).
- If the user asks "what is his position?" but does NOT include one of those words, position MUST be null.



Rules:
- Valid seasons: ["2021-22", "2022-23"]
- If the user mentions any other season (e.g. 2019, 2020, 2023-24), return season=null.
- If the user says "this season" or "last season", pick the closest valid season.
- Be tolerant to spelling mistakes. For example "halaand" should become "Erling Haaland"
  if that is clearly intended.
- If something is not clearly mentioned, keep it as null or empty list.
- Do NOT add comments, explanations, or extra text. Only output pure JSON.
- If (and only if) the TEXT contains words like "forward(s)" or "striker(s)", set position="FWD".
- Use position_filter ONLY if the user explicitly mentions a position group:
  forwards/strikers -> FWD, midfielders -> MID, defenders -> DEF, goalkeepers -> GK.
- If the user asks "what is his position?" (about a specific player), then put "position" in stats
  and keep position_filter = null.




Before you output JSON, silently verify:
- If none of the position keywords appear in TEXT, then position must be null.
- If you violate any rule, fix the JSON before outputting.
Return ONLY JSON.



TEXT: "{user_input}"

Return JSON:
"""

    response = client.chat_completion(
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=200,
    )

    content = response["choices"][0]["message"]["content"].strip()

    # Try to extract JSON even if model adds backticks, etc.
    try:
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            json_str = content[start:end + 1]
            data = json.loads(json_str)
        else:
            raise ValueError("No JSON found")
    except Exception:
        # Fallback if anything goes wrong
        data = {
            "players": [],
            "teams": [],
            "season": None,
            "gameweek": None,
            "position": None,
            "stats": [],
        }

    # Ensure all keys exist
    for key in ["players", "teams", "season", "gameweek", "position", "stats"]:
        data.setdefault(key, None if key in ["season", "gameweek", "position"] else [])

    # ----- Season validation against KG -----
    season = data.get("season")
    if season is not None and season not in VALID_SEASONS:
        data["season"] = None

    return data


def extract_entities(user_input: str) -> ParsedInput:
    """
    Main preprocessing function:
    - calls LLM NER to get entities
    - calls LLM classifier to get intent
    """
    entity_data = llm_extract_entities(user_input)

    entities = QueryEntities(
        players=entity_data.get("players", []),
        teams=entity_data.get("teams", []),
        season=entity_data.get("season"),
        gameweek=entity_data.get("gameweek"),
        position=entity_data.get("position"),
        stats=entity_data.get("stats", []),
    )

    intent = classify_intent(user_input)

    return ParsedInput(
        intent=intent,
        entities=entities,
        raw=user_input,
    )


# ---------- 1.c INPUT EMBEDDING ----------


# ---------- DEMO BLOCK ----------

if __name__ == "__main__":
    example_questions = [
        "Who is Mohamed Salah and what is his position?",

    ]

    
    for model_key in ["mini", "mpnet"]:
        print("\n" + "#" * 40)
        print(f"EMBEDDING MODEL: {model_key}")
        print("#" * 40)

        for q in example_questions:
            print("=" * 80)
            print("Q:", q)
            parsed = extract_entities(q)
            print(" -> intent (LLM):", parsed.intent)
            print(" -> entities:", parsed.entities)

            try:
                emb = embed(q, model_key=model_key)
                print(f" -> embedding length ({model_key}):", len(emb))
            except Exception as e:
                print(" -> embedding error:", e)

            print()
