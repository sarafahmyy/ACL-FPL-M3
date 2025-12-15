import streamlit as st
import sys
from pathlib import Path
from collections import defaultdict

sys.path.append(str(Path(__file__).resolve().parents[1]))  # add project root to path

from main import pipeline
from llm_factory import ModelCatalogue
from run_baseline import FORMATIONS  # ✅ uses your existing formations

MODEL_MAP = {
    "LLAMA_70B": ModelCatalogue.LLAMA_70B,
    "LLAMA_8B": ModelCatalogue.LLAMA_8B,
    "GPT_OSS": ModelCatalogue.GPT_OSS,
    "GPT_4": ModelCatalogue.GPT_4, 
    "GPT_35_TURBO": ModelCatalogue.GPT_35_TURBO,
    "GEMINI_FLASH": ModelCatalogue.GEMINI_FLASH,
    # add others if you have them
}

# Streamlit UI changes for retrieval method selection
st.set_page_config(page_title="FPL Graph-RAG", layout="wide")
st.title("⚽ FPL Graph-RAG Assistant")

# Sidebar controls
st.sidebar.header("Settings")
embedding_model_key = st.sidebar.selectbox("Embedding del", ["mini", "mpnet"], index=0)
llm_key_str = st.sidebar.selectbox("LLM", list(MODEL_MAP.keys()), index=0)
llm_key = MODEL_MAP[llm_key_str]

# ✅ NEW: mode toggle
mode = st.sidebar.radio("Mode", ["Q/A", "Recommender"], index=0)

# ✅ NEW: retrieval method selection
pipeline_mode = st.sidebar.selectbox("Select Retrieval Method", ["Both", "Baseline", "Embedding"], index=0)

# -------------------------
# Q/A MODE (your old UI)
# -------------------------
if mode == "Q/A":
    question = st.text_input("Ask a question:", value="Who is Mohamed Salah and what is his score?")
    run = st.button("Run")

    if run and question.strip():
        with st.spinner("Running pipeline..."):
            result = pipeline(
                question,
                llm_key=llm_key,
                embedding_model_key=embedding_model_key,
                pipeline_mode=pipeline_mode  # Pass selected pipeline mode
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

        # ---- RIGHT: Final Answer ----
        with col2:
            st.subheader("✅ Final LLM Answer")
            st.write(result.get("answer", "No answer returned"))

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

# -------------------------
# RECOMMENDER MODE (added)
# -------------------------
else:
    st.subheader("🏟 Team Recommender")

    formation = st.selectbox("Formation", list(FORMATIONS.keys()), index=0)
    team = st.text_input("Optional team filter (e.g. Liverpool, Arsenal)", value="")
    season = st.selectbox("Season", ["", "2021-22", "2022-23"], index=2)

    run = st.button("Build Team")

    if run:
        rec_question = f"Build me a {formation} team"
        if team.strip():
            rec_question += f" for {team.strip()}"
        if season:
            rec_question += f" in {season}"

        with st.spinner("Running pipeline..."):
            result = pipeline(
                rec_question,
                llm_key=llm_key,
                embedding_model_key=embedding_model_key,
                pipeline_mode=pipeline_mode  # Pass selected pipeline mode
            )

        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("🔎 KG Retrieved Context (Raw)")

            baseline = result.get("baseline", {})
            rows = baseline.get("rows", [])
            st.write("**Rows returned:**", len(rows))
            st.json(rows[:50])

            st.subheader("🧾 Cypher Query Executed (Optional)")
            st.code(baseline.get("query", "No Cypher query"), language="cypher")
            st.write("**Params:**")
            st.json(baseline.get("params", {}))

            st.subheader("🧠 Vector Search Results (Optional)")
            embedding = result.get("embedding", {})
            st.json(embedding.get("rows", [])[:20])

            st.subheader("🧩 Combined Chunks (Deduped)")
            st.json(result.get("combined", [])[:60])

        with col2:
            st.subheader("✅ Recommended Team")

            if result.get("intent") == "team_formulation":
                baseline = result.get("baseline", {})

                st.write("**Formation:**", baseline.get("formation_str", formation))
                if baseline.get("team"):
                    st.write("**Team filter:**", baseline.get("team"))
                st.write("**Season:**", baseline.get("season"))

                # --- Starting XI ---
                st.markdown("## ✅ Starting XI (Final Team)")
                xi = baseline.get("xi", [])
                if not xi:
                    st.warning("No XI returned for this recommender query.")
                else:
                    # display by position
                    for pos in ["GK", "DEF", "MID", "FWD"]:
                        pos_rows = [p for p in xi if p.get("position") == pos]
                        if pos_rows:
                            st.markdown(f"### {pos}")
                            st.table([{
                                "player": r.get("player"),
                                "total_points": r.get("total_points"),
                                "appearances": r.get("appearances"),
                                "goals": r.get("goals"),
                                "assists": r.get("assists"),
                                "explanation": r.get("explanation"),
                            } for r in pos_rows])

                # --- Ranked Pool ---
                st.markdown("## 📌 Ranked Recommendations (Candidate Pool)")
                rows = baseline.get("rows", [])
                if not rows:
                    st.warning("No ranked pool returned.")
                else:
                    for pos in ["GK", "DEF", "MID", "FWD"]:
                        pos_rows = [r for r in rows if r.get("position") == pos]
                        if pos_rows:
                            st.markdown(f"### {pos} candidates")
                            st.table([{
                                "rank_in_position": r.get("rank_in_position"),
                                "player": r.get("player"),
                                "total_points": r.get("total_points"),
                                "appearances": r.get("appearances"),
                                "goals": r.get("goals"),
                                "assists": r.get("assists"),
                                "selected_in_xi": r.get("selected_in_xi"),
                                "explanation": r.get("explanation"),
                            } for r in pos_rows])

            else:
                st.warning("Recommender intent was not detected. Showing normal answer instead.")
                st.write(result.get("answer", "No answer returned"))
                
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
