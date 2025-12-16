from typing import Optional

from feature_embeddings import semantic_player_search
from intent_entity import extract_entities







user_questions = [
        "how many points did  cr7 score in last seasons",
        "tell me forwards from the gunners",
        "Who is Momo Salah?",
        "Top forwards in 2022/23 season",
        "Show me stats and goals for kdb in 2022-23",
        "How many points did Haaland get in GW 3 2022-23?",
        "Tell me about spurs",
        "give me 4 midfielders from arsenal",
        "how did the egyption king perform ",
        "Show me stats and goals for midfielders in 2022-23",
        "who is halaand?",
        "compare between mohamed salah and harry kane performance in 2021-22 season",
        "ايه هي ارقام صارؤخ ماضيلرا في الموسم اللي فات",
        
        
    ]

output={}
    
for embedding_model in ["text-embedding-3-large", "text-embedding-3-small"]:
    embedding_output=[]
    for q in user_questions:
        print("=" * 50)
        print(f"Using embedding model: {embedding_model} \n on question: {q}")
        
        parsed_intents_entities = extract_entities(q)

        embedding_result = semantic_player_search(parsed_intents_entities, model_key=embedding_model, k=5)
        response = embedding_result.get("rows", [])

        print("Response:", response)
        embedding_output.append({"question":q,
                           "response":response,
                           })
    output[embedding_model]=embedding_output


def format_results_to_markdown(output_dict):
    """
    Format the embedding comparison results into markdown.
    
    Args:
        output_dict: Dictionary with model names as keys and list of results as values
    
    Returns:
        Markdown formatted string
    """
    markdown = "# Embedding Model Comparison Results\n\n"
    
    # Summary table
    markdown += "## Summary\n\n"
    markdown += "| Model | Questions Processed | Total Results |\n"
    markdown += "|-------|--------------------:|--------------:|\n"
    
    for model_name, results in output_dict.items():
        total_results = sum(len(r['response']) for r in results)
        markdown += f"| {model_name} | {len(results)} | {total_results} |\n"
    
    markdown += "\n---\n\n"
    
    # Detailed results for each question
    for question_idx, question in enumerate(user_questions, 1):
        markdown += f"## Question {question_idx}: {question}\n\n"
        
        for model_name in output_dict.keys():
            markdown += f"### Model: {model_name}\n\n"
            
            # Find the results for this question
            result = next((r for r in output_dict[model_name] if r['question'] == question), None)
            
            if result and result['response']:
                markdown += "| Rank | Player | Position | confidence |\n"
                markdown += "|-----:|--------|----------|------:|\n"
                
                for rank, row in enumerate(result['response'], 1):
                    player = row.get('player', 'N/A')
                    position = row.get('position', 'N/A')
                    confidence = row.get('confidence', 0)
                    markdown += f"| {rank} | {player} | {position} | {confidence:.4f} |\n"
            else:
                markdown += "No results found\n"
            
            markdown += "\n"
        
        markdown += "---\n\n"
    
    # Model-by-model detailed view
    markdown += "## Detailed Results by Model\n\n"
    
    for model_name, results in output_dict.items():
        markdown += f"### {model_name}\n\n"
        
        for result in results:
            question = result['question']
            response = result['response']
            
            markdown += f"*Question:* {question}\n\n"
            
            if response:
                markdown += "| Rank | Player | Position | confidence |\n"
                markdown += "|-----:|--------|----------|------:|\n"
                
                for rank, row in enumerate(response, 1):
                    player = row.get('player', 'N/A')
                    position = row.get('position', 'N/A')
                    confidence = row.get('confidence', 0)
                    markdown += f"| {rank} | {player} | {position} | {confidence:.4f} |\n"
            else:
                markdown += "No results found\n"
            
            markdown += "\n"
        
        markdown += "---\n\n"
    
    return markdown


# Generate markdown report
markdown_output = format_results_to_markdown(output)

# Save to file
output_filename = "embedding_comparison_results.md"
with open(output_filename, 'w',encoding="utf-8") as f:
    f.write(markdown_output)

print("\n" + "=" * 60)
print(f"✅ Results saved to '{output_filename}'")
print("=" * 60)

# Also print to console
print("\n" + markdown_output)