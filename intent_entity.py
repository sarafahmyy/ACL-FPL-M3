from dataclasses import dataclass, field
from typing import List, Optional
import re
import os

from huggingface_hub import InferenceClient
from sentence_transformers import SentenceTransformer


# ---------- DATA STRUCTURES (used for 1.b) ----------

@dataclass
class QueryEntities:
    """
    Holds all FPL-related entities we can extract from the user input.
    """
    players: List[str] = field(default_factory=list)
    teams: List[str] = field(default_factory=list)
    season: Optional[str] = None
    gameweek: Optional[int] = None
    position: Optional[str] = None
    stats: List[str] = field(default_factory=list)


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
    "greetings"
]

def classify_intent(user_input: str) -> str:
    """
    Uses the LLM (Gemma 2B IT) to classify the user's intent.
    Extended with 'player_identity' intent.
    """
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        raise RuntimeError("HF_TOKEN environment variable not set!")

    client = InferenceClient(
        model="google/gemma-2-2b-it",
        token=hf_token
    )

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




# ---------- 1.b ENTITY EXTRACTION HELPERS ----------

KNOWN_POSITIONS = {
    "goalkeeper": "GK",
    "keeper": "GK",
    "gk": "GK",
    "defender": "DEF",
    "def": "DEF",
    "midfielder": "MID",
    "mid": "MID",
    "forward": "FWD",
    "striker": "FWD",
    "fwd": "FWD",
}

STAT_KEYWORDS_TO_PROP = {
    "points": "total_points",
    "total points": "total_points",
    "goals": "goals_scored",
    "goals scored": "goals_scored",
    "assists": "assists",
    "minutes": "minutes",
    "yellow cards": "yellow_cards",
    "red cards": "red_cards",
    "clean sheets": "clean_sheets",
}


def extract_season(text: str) -> Optional[str]:
    m = re.search(r"(20\d{2}-\d{2})", text)
    if m:
        return m.group(1)

    for year in ["2021", "2022", "2023", "2024"]:
        if year in text:
            return year

    return None


def extract_gameweek(text: str) -> Optional[int]:
    m = re.search(r"(gw|gameweek)\s*([0-9]{1,2})", text)
    if m:
        return int(m.group(2))
    return None


def extract_position(text: str) -> Optional[str]:
    for word, code in KNOWN_POSITIONS.items():
        if word in text:
            return code
    return None


def extract_stats(text: str) -> List[str]:
    found = []
    for phrase, prop in STAT_KEYWORDS_TO_PROP.items():
        if phrase in text:
            if prop not in found:
                found.append(prop)
    return found


def extract_players_and_teams(text: str) -> tuple[list[str], list[str]]:
    """
    Placeholder — for now, no name detection.
    """
    return [], []


# ---------- MAIN ENTITY EXTRACTION + INTENT ----------

def extract_entities(user_input: str) -> ParsedInput:
    text_lower = user_input.lower()

    season = extract_season(text_lower)
    gw = extract_gameweek(text_lower)
    position = extract_position(text_lower)
    stats = extract_stats(text_lower)
    players, teams = extract_players_and_teams(user_input)

    entities = QueryEntities(
        players=players,
        teams=teams,
        season=season,
        gameweek=gw,
        position=position,
        stats=stats,
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
        "How many points did Haaland get in GW 3 2022-23?",
        "How did Arsenal team perform last season?",
        "Who should I captain this gameweek?",
        "What is the next fixture for Liverpool in GW 10?",
        "Show me stats and goals for midfielders in 2022-23",
        "who is halaand?",
        "who should i captin",
        "hello there how are you?",
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
