from dataclasses import dataclass, field
from typing import List, Optional
import os
import json

from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer


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


# ---------- 1.a INTENT CLASSIFICATION (LLM ONLY) ----------

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


# ---------- 1.b ENTITY EXTRACTION (LLM NER, NO RULES) ----------

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
  "position": null,// one of "GK", "DEF", "MID", "FWD" or null
  "stats": []      // list of property names like:
                  // "total_points", "goals_scored", "assists",
                  // "minutes", "yellow_cards", "red_cards", "clean_sheets"
}}

Rules:
- Valid seasons: ["2021-22", "2022-23"]
- If the user mentions any other season (e.g. 2019, 2020, 2023-24), return season=null.
- If the user says "this season" or "last season", pick the closest valid season.
- Be tolerant to spelling mistakes. For example "halaand" should become "Erling Haaland"
  if that is clearly intended.
- If the user mentions "forwards", "strikers", etc., map the position to "FWD".
- If something is not clearly mentioned, keep it as null or empty list.
- Do NOT add comments, explanations, or extra text. Only output pure JSON.

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

_embedding_model = None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def embed_input(user_input: str):
    model = get_embedding_model()
    vec = model.encode(user_input)
    return vec.tolist()


# ---------- DEMO BLOCK ----------

if __name__ == "__main__":
    example_questions = [
        "Top forwards in 2023 season",
        "Show me stats and goals for midfielders in 2019",
        "How many points did Haaland get in GW 3 2022-23?",
        "How did Arsenal team perform last season?",
        "Who should I captain this gameweek?",
        "What is the next fixture for Liverpool in GW 10?",
        "Show me stats and goals for midfielders in 2022-23",
        "who is halaand?",
        "Who could I captin this gameweek?",
        "hello there how are you?"
    ]

    for q in example_questions:
        print("=" * 80)
        print("Q:", q)
        parsed = extract_entities(q)
        print(" -> intent (LLM):", parsed.intent)
        print(" -> entities:", parsed.entities)

        try:
            emb = embed_input(q)
            print(" -> embedding length:", len(emb))
        except Exception as e:
            print(" -> embedding error:", e)

        print()
