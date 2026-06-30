import os
import json
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Exploration.utils import parse_response
from Exploration.my_llm import chat_my

TOOL_DESC_PATH = "tool_metadata/tool_description.json"
TEST_QUERIES_PATH = "data/test_split_queries.json"
RESULTS_PATH = "results/unsplit_test_results.json"
MODEL_CKPT = "llama3.1:8b-instruct-fp16"

BACKGROUND_APIS = [
    "verify_email", "get_car_makes", "get_animal_facts", 
    "search_public_restrooms", "get_dog_breeds_metadata", 
    "get_financial_data", "get_media_news", "search_arxiv_papers", 
    "get_weather_forecast", "calculate_mortgage_payment", 
    "get_divisions_near_location"
]

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_test():
    tool_desc = load_json(TOOL_DESC_PATH)
    queries = load_json(TEST_QUERIES_PATH)
    
    with open("prompts/prompt_template.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()
        
    results = []
    
    for idx, q in enumerate(queries):
        query_text = q["query"]
        target_api = q["target_api"]
        
        print(f"\n[{idx+1}/{len(queries)}] Query: {query_text}")
        
        api_names_list = list(BACKGROUND_APIS)
        if target_api == "get_restaurants_by_location":
            api_names_list.append("get_hotels_by_location")
        elif target_api == "get_hotels_by_location":
            api_names_list.append("get_restaurants_by_location")
            
        api_names_list.append(target_api)
        api_names_list = list(set(api_names_list))
        random.shuffle(api_names_list)
        
        context_apis_str = []
        target_api_desc = None
        for current_api in api_names_list:
            desc = tool_desc[current_api]
            if current_api == target_api:
                target_api_desc = desc
            context_apis_str.append(f"API_name: {current_api}\nDescription:\n{json.dumps(desc, indent=2, ensure_ascii=False)}")
            
        api_descriptions_full = "\n\n".join(context_apis_str)
        prompt_base = prompt_template.format(
            api_descriptions=api_descriptions_full,
            api_names="\n".join(api_names_list)
        )
        prompt = prompt_base + "\n\nUser Query: " + query_text
        
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        messages, _ = chat_my(messages, prompt, visualize=False, model=MODEL_CKPT, return_tokens=True)
        model_output = messages[-1]["content"]
        
        parsed = parse_response(model_output, api_names_list, json.dumps(target_api_desc), check_API_name=True)
        
        is_success = parsed["parse_successful"] and parsed["action"] == target_api
        if is_success:
            print(f"  [HIT] Action: {parsed['action']}")
        else:
            print(f"  [MISS] Result: {parsed.get('parse_error_msg', 'Wrong API')}")
            
        results.append({
            "query_id": q["id"],
            "query": query_text,
            "target_api": target_api,
            "model_output": model_output,
            "parsed_result": parsed,
            "is_success": is_success
        })
            
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\n📦 Saved evaluation results to {RESULTS_PATH}")

if __name__ == "__main__":
    run_test()
