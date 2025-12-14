import streamlit as st
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.embedding import get_available_embedding_keys
sys.path.append(str(Path(__file__).resolve().parents[1]))  # add project root to path
from main import pipeline
from llm_factory import ModelCatalogue

MODEL_MAP = {
    "LLAMA_70B": ModelCatalogue.LLAMA_70B,
    "LLAMA_8B": ModelCatalogue.LLAMA_8B,
    "GPT_OSS": ModelCatalogue.GPT_OSS,
    "GPT_4": ModelCatalogue.GPT_4,
    "GPT_35_TURBO": ModelCatalogue.GPT_35_TURBO,
    "GEMINI_FLASH": ModelCatalogue.GEMINI_FLASH,
    # add others if you have them
}



embedding_keys = get_available_embedding_keys()




st.set_page_config(page_title="FPL Graph-RAG", layout="wide")

st.title("⚽ FPL Graph-RAG Assistant")

# Sidebar controls
st.sidebar.header("Settings")

embedding_model_key = st.sidebar.selectbox(
    "Embedding model",
    embedding_keys,
    index=0
)

llm_key_str = st.sidebar.selectbox("LLM", list(MODEL_MAP.keys()), index=0)
llm_key = MODEL_MAP[llm_key_str]


question = st.text_input("Ask a question:", value="Who is Mohamed Salah and what is his score?")

run = st.button("Run")

if run and question.strip():
    with st.spinner("Running pipeline..."):
        result = pipeline(
            question,
            llm_key=llm_key,                
            embedding_model_key=embedding_model_key
        )

    # Layout: 2 columns
    col1, col2 = st.columns([1, 1])

    # ---- LEFT: Retrieval transparency ----
    with col1:
        st.subheader("🔎 KG Retrieved Context (Raw)")

        baseline = result.get("baseline", {})
        rows = baseline.get("rows", [])
        st.write("**Rows returned:**", len(rows))
        st.json(rows[:20])  # show first 20 rows

        st.subheader("🧾 Cypher Query Executed (Optional)")
        st.code(baseline.get("query", "No Cypher query"), language="cypher")
        st.write("**Params:**")
        st.json(baseline.get("params", {}))

        st.subheader("🧠 Vector Search Results (Optional)")
        embedding = result.get("embedding", {})
        st.json(embedding.get("rows", [])[:20])

        st.subheader("🧩 Combined Chunks (Deduped)")
        st.json(result.get("combined", [])[:40])

    # ---- RIGHT: Final Output ----
    with col2:
        st.subheader("✅ Final Output")

        # ===== TEAM FORMULATION DISPLAY =====
        if result.get("intent") == "team_formulation":
            st.subheader("🏟 Recommended Team Formation")

            formation = result.get("baseline", {}).get("formation", "N/A")
            st.write(f"**Formation:** {formation}")

            rows = result.get("baseline", {}).get("rows", [])

            # group flat rows back by position
            grouped_team = defaultdict(list)
            for r in rows:
                grouped_team[r.get("position", "UNK")].append(r)

            for pos, players in grouped_team.items():
                st.markdown(f"### {pos}")
                st.table(players)

        # ===== NORMAL QA DISPLAY =====
        else:
            st.subheader("🧠 Final LLM Answer")
            st.write(result.get("answer", "No answer returned"))

        # ===== PARSED INFO =====
        st.subheader("🧾 Parsed Intent & Entities")
        st.write("**Intent:**", result.get("intent"))

        entities = result.get("entities")

        if hasattr(entities, "model_dump"):
            st.json(entities.model_dump())
        elif hasattr(entities, "dict"):
            st.json(entities.dict())
        elif hasattr(entities, "__dict__"):
            st.json(vars(entities))
        else:
            st.json(entities)


