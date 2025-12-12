import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))  # add project root to path
from main import pipeline
from llm_factory import ModelCatalogue

MODEL_MAP = {
    "LLAMA_70B": ModelCatalogue.LLAMA_70B,
    "LLAMA_8B": ModelCatalogue.LLAMA_8B,
    # add others if you have them
}



st.set_page_config(page_title="FPL Graph-RAG", layout="wide")

st.title("⚽ FPL Graph-RAG Assistant")

# Sidebar controls
st.sidebar.header("Settings")
embedding_model_key = st.sidebar.selectbox("Embedding del", ["mini", "mpnet"], index=0)
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

    # ---- RIGHT: Final Answer ----
    with col2:
      st.subheader("✅ Final LLM Answer")
      st.write(result.get("answer", "No answer returned"))

      st.subheader("🧾 Parsed Intent & Entities")
      st.write("**Intent:**", result.get("intent"))

      entities = result.get("entities")

    # render entities safely
      if hasattr(entities, "model_dump"):          # Pydantic v2
        st.json(entities.model_dump())
      elif hasattr(entities, "dict"):             # Pydantic v1
        st.json(entities.dict())
      elif hasattr(entities, "__dict__"):         # normal class/dataclass
        st.json(vars(entities))
      else:
        st.json(entities)


