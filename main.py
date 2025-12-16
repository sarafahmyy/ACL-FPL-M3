
from feature_embeddings import semantic_player_search
from intent_entity import ParsedInput, QueryEntities, extract_entities
from run_baseline import route_baseline
from llm_factory import LLMFactory, ModelCatalogue
from utils.pipeline_utils import combine_chunks
from typing import Optional




def pipeline(
    user_question: str,
    llm_key=ModelCatalogue.LLAMA_70B,
    embedding_model_key: str = "text-embedding-3-large",
    mode: str = "qa",
    formation: str = "3-4-3",
    team: Optional[str] = None,
    season: Optional[str] = None,
    pipeline_mode: str = "Both",  # New argument to specify retrieval method
):

    llm = LLMFactory(llm_key)
    llm.set_system_message("""
You are a highly knowledgeable assistant specialized in Fantasy Premier League (FPL) data analysis. Your role is to provide users with insightful, accurate, and actionable answers related to FPL statistics, player performance, team recommendations, and other FPL-related queries. You can analyze historical player data, compare player stats, suggest team formations, and assist with fantasy football strategies. Always provide clear and concise answers based on the context given, and do not make assumptions outside of the provided information, also respond to greetings in a polite way.
""")

    print("\n--- EXTRACTING INTENT AND ENTITIES ---")

    if mode == "recommender":
        # Same recommender logic here...
        entities = QueryEntities(
            teams=[team] if team else [],
            season=season,
            position=None,
            players=[],
            stats=[],
            gameweek=None,
        )

        raw = f"Build me a {formation} team"
        if team:
            raw += f" for {team}"
        if season:
            raw += f" in {season}"

        parsed = ParsedInput(intent="team_formulation", entities=entities, raw=raw)

        baseline_result = route_baseline(parsed)   
        return {
            "answer": None,                         
            "intent": "team_formulation",
            "entities": entities,
            "baseline": baseline_result,
            "embedding": {},
            "combined": [],
            "input_tokens": llm.get_token_usage()['input_tokens'],
            "output_tokens": llm.get_token_usage()['output_tokens'],
        }

    parsed_intents_entities = extract_entities(user_question)

    print("\n--- EXTRACTED INTENT AND ENTITIES ---")
    print("Intent:", parsed_intents_entities.intent)
    print("Entities:", parsed_intents_entities.entities)

    print("\n--- RUNNING RETRIEVAL ---")
    
    baseline_result = {}
    embedding_result = {}

    # Handle retrieval based on selected method
    try:
        if pipeline_mode in ["Both", "Baseline"]:
            baseline_result = route_baseline(parsed_intents_entities)
            baseline_chunks = baseline_result.get("rows", [])
        else:
            baseline_chunks = []

    except Exception as e:
        print("\n[ERROR RUNNING BASELINE RETRIEVAL]", e)
        print()
        baseline_chunks = []

    try:
        if pipeline_mode in ["Both", "Embedding"]:
            embedding_result = semantic_player_search(parsed_intents_entities, model_key=embedding_model_key, k=5)
            embedding_chunks = embedding_result.get("rows", [])
        else:
            embedding_chunks = []

    except Exception as e:
        print("\n[ERROR RUNNING EMBEDDING RETRIEVAL]", e)
        print()
        embedding_chunks = []
        
    print("\n--- COMBINING RESULTS ---")
    combined_chunks = combine_chunks(baseline_chunks, embedding_chunks)
    print("Combined context:\n", combined_chunks)

    prompt = f"""
You are a highly knowledgeable assistant specializing in Fantasy Premier League (FPL). You have access to context from FPL-related knowledge sources. Given the user question and the context chunks retrieved from the knowledge base, provide a concise and accurate answer. If the answer is not directly available, respond with 'I don't know'. Do not make up information, and avoid providing details not found in the context. 

User Question: {user_question}

Context Chunks:
{combined_chunks}

Your Response:
"""


    response = llm.send_to_llm(prompt)
    
    return {
      "answer": response,
      "intent": parsed_intents_entities.intent,
      "entities": parsed_intents_entities.entities,
      "baseline": baseline_result,     
      "embedding": embedding_result,    
      "combined": combined_chunks,
      "input_tokens": llm.get_token_usage()['input_tokens'],
      "output_tokens": llm.get_token_usage()['output_tokens'],
}
        
        
    

    



#if __name__ == "__main__":
    # example_questions = [
    #     "Top forwards in 2023 season",
    #     "Show me stats and goals for midfielders in 2022-23",
    #     "How many points did Haaland get in GW 3 2022-23?",
    #     "How did Arsenal team perform last season?",
    #     "give me 4 midfielders from arsenal",
    #     "Who did Liverpool face in GW 10 season 2021-22?",
    #     "Show me stats and goals for midfielders in 2022-23",
    #     "who is halaand?",
    #     "compare between mohamed salah and harry kane performance in 2021-22 season",
    #     "who is the top scorer in 2022-23 season?",
    #     "hello there how are you?"
    # ]


    #embedding_model_key=""
    #user_question="who is mo salah and where does he play and what is his score?"
    #llm=ModelCatalogue.LLAMA_70B

    #response = pipeline(user_question, llm_key=llm, embedding_model_key=embedding_model_key)
    #print("\n--- FINAL RESPONSE ---")
    #print(response)

