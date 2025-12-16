import time

from llm_factory import  ModelCatalogue
from main import pipeline
# user_questions = [
#         "Top forwards in 2023 season",
#         "Show me stats and goals for midfielders in 2022-23",
#         "How many points did Haaland get in GW 3 2022-23?",
#         "How did Arsenal team perform last season?",
#         "give me 4 midfielders from arsenal",
#         "Who did Liverpool face in GW 10 season 2021-22?",
#         "Show me stats and goals for midfielders in 2022-23",
#         "who is halaand?",
#         "compare between mohamed salah and harry kane performance in 2021-22 season",
#         "who is the top scorer in 2022-23 season?",
#         "hello there how are you?"
#     ]

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
    
for llm_model in [ModelCatalogue.LLAMA_70B,ModelCatalogue.GPT_35_TURBO,ModelCatalogue.GPT_4]:
    llm_output=[]
    for q in user_questions:
        start=time.time()
        print("=" * 50)
        print(f"Using model: {llm_model.name} \n on question: {q}")
        # llm = LLMFactory(model=llm_model)
        try:
            response =pipeline(
                q,
                llm_key=llm_model,
            )
            end=time.time()
            time_taken = round(end - start, 2)
        except Exception as e:
            print(f"Error with model {llm_model.name} on question '{q}': {e}")
            response = {"answer": "Error occurred", "input_tokens": 0, "output_tokens": 0}
            time_taken = "N/A"

        llm_output.append({"question":q,
                           "response":response["answer"],
                           "time_taken":f"{time_taken} seconds",
                           "input_tokens":response['input_tokens'],
                           "output_tokens":response['output_tokens'],})
    output[llm_model.name]=llm_output
    


    # Pricing per million tokens (in USD)
MODEL_PRICING = {
    "GPT_4": {
        "input": 30.00,   # $30.00 per million input tokens
        "output": 60.00   # $60.00 per million output tokens
    },
    "GPT_35_TURBO": {
        "input": 0.50,    # $0.50 per million input tokens
        "output": 1.50    # $1.50 per million output tokens
    },
    "LLAMA_70B": {
        "input": 0.00,    # Free
        "output": 0.00
    },
    "LLAMA_8B": {
        "input": 0.00,    # Free
        "output": 0.00
    },
    "GPT_OSS": {
        "input": 0.00,    # Free
        "output": 0.00
    },
    "GEMINI_FLASH": {
        "input": 0.00,    # Free
        "output": 0.00
    }
}

def calculate_cost(model_name, input_tokens, output_tokens):
    """
    Calculate the cost for a given model and token usage.
    
    Args:
        model_name: Name of the model
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        Cost in USD
    """
    if model_name not in MODEL_PRICING:
        return 0.0
    
    pricing = MODEL_PRICING[model_name]
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    
    return input_cost + output_cost

# Calculate total costs for each model
print("=" * 60)
print("Cost Analysis")
print("=" * 60)

for model_name, results in output.items():
    total_input_tokens = sum(r['input_tokens'] for r in results)
    total_output_tokens = sum(r['output_tokens'] for r in results)
    total_cost = calculate_cost(model_name, total_input_tokens, total_output_tokens)
    
    cost_label = "FREE" if total_cost == 0 else f"${total_cost:.6f}"
    
    print(f"\n{model_name}:")
    print(f"  Total Input Tokens:  {total_input_tokens:,}")
    print(f"  Total Output Tokens: {total_output_tokens:,}")
    print(f"  Total Cost: {cost_label}")
    
print("\n" + "=" * 60)



def output_to_markdown(output_dict):
    """
    Convert the output dictionary to a markdown table with performance and cost analysis.
    
    Args:
        output_dict: Dictionary with model names as keys and list of results as values
    
    Returns:
        Markdown formatted string
    """
    markdown = "# LLM Comparison Results\n\n"
    
    # Add performance and cost summary table
    markdown += "## Performance & Cost Analysis\n\n"
    markdown += "| Model | Total Time | Avg Time/Run | Total Input Tokens | Total Output Tokens | Avg Input/Run | Avg Output/Run | Total Cost | Avg Cost/Run |\n"
    markdown += "|-------|----------:|-----------:|------------------:|-------------------:|-------------:|-------------:|----------:|------------:|\n"
    
    for model_name, results in output_dict.items():
        # Calculate time metrics
        total_time = sum(float(r['time_taken'].replace(' seconds', '')) for r in results)
        num_runs = len(results)
        avg_time_per_run = total_time / num_runs if num_runs > 0 else 0
        
        # Calculate token metrics
        total_input_tokens = sum(r['input_tokens'] for r in results)
        total_output_tokens = sum(r['output_tokens'] for r in results)
        avg_input_per_run = total_input_tokens / num_runs if num_runs > 0 else 0
        avg_output_per_run = total_output_tokens / num_runs if num_runs > 0 else 0
        
        # Calculate cost metrics
        total_cost = calculate_cost(model_name, total_input_tokens, total_output_tokens)
        avg_cost_per_run = total_cost / num_runs if num_runs > 0 else 0
        
        cost_label = "FREE" if total_cost == 0 else f"${total_cost:.6f}"
        avg_cost_label = "FREE" if avg_cost_per_run == 0 else f"${avg_cost_per_run:.6f}"
        
        markdown += f"| {model_name} | {total_time:.2f}s | {avg_time_per_run:.2f}s | {total_input_tokens:,} | {total_output_tokens:,} | {avg_input_per_run:.1f} | {avg_output_per_run:.1f} | {cost_label} | {avg_cost_label} |\n"
    
    markdown += "\n---\n\n"
    
    # Add detailed results per model
    for model_name, results in output_dict.items():
        markdown += f"## {model_name}\n\n"
        markdown += "| Question | Response | Time Taken | Input Tokens | Output Tokens |\n"
        markdown += "|----------|----------|------------|--------------|---------------|\n"
        
        for result in results:
            question = result['question'].replace('|', '\\|')  # Escape pipes in text
            response = result['response'].replace('|', '\\|').replace('\n', ' ')[:100] + "..."  # Truncate long responses
            time_taken = result['time_taken']
            input_tokens = result['input_tokens']
            output_tokens = result['output_tokens']
            
            markdown += f"| {question} | {response} | {time_taken} | {input_tokens} | {output_tokens} |\n"
        
        markdown += "\n"
    
    return markdown


# Generate markdown table
markdown_output = output_to_markdown(output)

with open("llm_comparison_results.md", "w", encoding="utf-8") as f:
    f.write(f"{markdown_output}")
print(markdown_output)