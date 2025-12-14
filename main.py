
from feature_embeddings import semantic_player_search
from intent_entity import extract_entities
from run_baseline import route_baseline
from llm_factory import LLMFactory, ModelCatalogue
from utils.pipeline_utils import combine_chunks



def pipeline(user_question: str,
             llm_key=ModelCatalogue.LLAMA_70B,
            embedding_model_key: str = "mini"
            ):
    
    llm = LLMFactory(llm_key)
    llm.set_system_message("You are a helpful assistant specialized in Fantasy Premier League (FPL) data retrieval and analysis.")


    print("\n--- EXTRACTING INTENT AND ENTITIES ---")

    parsed_intents_entities = extract_entities(user_question)

    print("\n--- EXTRACTED INTENT AND ENTITIES ---")
    print("Intent:", parsed_intents_entities.intent)
    print("Entities:", parsed_intents_entities.entities)



    print("\n--- RUNNING BASELINE APPROACH ---")


    baseline_result = {}
    embedding_result = {}


    try:
        baseline_result = route_baseline(parsed_intents_entities)
        baseline_chunks = baseline_result.get("rows", [])

    except Exception as e:
        print("\n[ERROR RUNNING BASELINE RETRIEVAL]", e)
        print()
        baseline_chunks= []

    try:
        embedding_result = semantic_player_search(parsed_intents_entities, model_key=embedding_model_key, k=5)
        embedding_chunks = embedding_result.get("rows", [])


    except Exception as e:
        print("\n[ERROR RUNNING EMBEDDING RETRIEVAL]", e)
        print()
        embedding_chunks = []
        
    print("\n--- COMBINING RESULTS ---")
    combined_chunks = combine_chunks(baseline_chunks, embedding_chunks)
    print("Combined context:\n", combined_chunks)

    prompt=f""" given the following user question: {user_question}
    and the following context chunks from the knowledge base:
    {combined_chunks}
    Provide a concise answer to the user question based on the context chunks.
    If the answer is not found in the context, respond with 'I don't know'.
    do not fabricate any information or make up answers or respond from your own knowledge."""

    response = llm.send_to_llm(prompt)
    
    return {
      "answer": response,
      "intent": parsed_intents_entities.intent,
      "entities": parsed_intents_entities.entities,
      "baseline": baseline_result,     
      "embedding": embedding_result,    
      "combined": combined_chunks,
}






#if __name__ == "__main__":
    # example_questions = [
    #     "Top forwards in 2023 season",
    #     "Show me stats and goals for midfielders in 2019",
    #     "How many points did Haaland get in GW 3 2022-23?",
    #     "How did Arsenal team perform last season?",
    #     "Who should I captain this gameweek?",
    #     "What is the next fixture for Liverpool in GW 10?",
    #     "Show me stats and goals for midfielders in 2022-23",
    #     "who is halaand?",
    #     "Who could I captin this gameweek?",
    #     "hello there how are you?"
    # ]


    #embedding_model_key="mini"
    #user_question="who is mo salah and where does he play and what is his score?"
    #llm=ModelCatalogue.LLAMA_70B

    #response = pipeline(user_question, llm_key=llm, embedding_model_key=embedding_model_key)
    #print("\n--- FINAL RESPONSE ---")
    #print(response)

