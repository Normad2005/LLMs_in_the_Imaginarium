import os
import json
import sys

# Ensure we can import from the parent directory / other files
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Exploration.utils import parse_response
from Exploration.my_llm import chat_my

# Configuration
TOOL_DESC_PATH = "tool_metadata/tool_description.json"
INTENT_DEF_PATH = "results/intent_definitions.json"
TEST_QUERIES_PATH = "data/test_split_queries.json"
RESULTS_PATH = "results/split_test_results.json"
MODEL_CKPT = "llama3.1:8b-instruct-fp16"

# Background noise APIs
BACKGROUND_APIS = [
    "verify_email",
    "get_car_makes",
    "get_animal_facts",
    "search_public_restrooms",
    "get_dog_breeds_metadata",
    "get_financial_data",
    "get_media_news",
    "search_arxiv_papers",
    "get_weather_forecast",
    "calculate_mortgage_payment",
    "get_divisions_near_location"
]

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_api_context(api_name, intent_id=None, tool_desc=None, intent_defs=None):
    """
    Builds the API description dictionary.
    If intent_id is provided, returns the filtered 'split' API.
    Otherwise, returns the full 'unsplit' API.
    """
    if tool_desc is None:
        tool_desc = load_json(TOOL_DESC_PATH)
    if intent_defs is None:
        intent_defs = load_json(INTENT_DEF_PATH)

    original_api = tool_desc.get(api_name)
    if not original_api:
        raise ValueError(f"API {api_name} not found in tool descriptions.")

    if intent_id is None:
        return original_api # Return unsplit (Group A)

    # Return split (Group B)
    intents = intent_defs.get(api_name, {}).get("intents", [])
    target_intent = next((i for i in intents if i["intent_id"] == intent_id), None)
    if not target_intent:
        raise ValueError(f"Intent {intent_id} not found for {api_name}.")

    filtered_api = {
        "description": target_intent["description"],
        "required_parameters": [],
        "optional_parameters": []
    }
    
    key_params = target_intent.get("key_parameters", [])
    
    for param in original_api.get("required_parameters", []):
        if param["name"] in key_params:
            filtered_api["required_parameters"].append(param)
            
    for param in original_api.get("optional_parameters", []):
        if param["name"] in key_params:
            filtered_api["optional_parameters"].append(param)

    return filtered_api

def run_test():
    tool_desc = load_json(TOOL_DESC_PATH)
    intent_defs = load_json(INTENT_DEF_PATH)
    queries = load_json(TEST_QUERIES_PATH)
    
    with open("prompts/prompt_template.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()
        
    results = []
    
    import random

    for q in queries:
        query_text = q["query"]
        target_api = q["target_api"]
        target_intent_id = q["target_intent_id"]
        
        print(f"\n=====================================")
        print(f"Testing Query: {query_text}")
        
        # Determine randomized order once per query for fairness
        api_names_list = list(BACKGROUND_APIS)
        if target_api == "get_restaurants_by_location":
            api_names_list.append("get_hotels_by_location") # Strong distractor
        elif target_api == "get_hotels_by_location":
            api_names_list.append("get_restaurants_by_location")
            
        api_names_list.append(target_api)
        
        # Deduplicate while preserving list
        unique_apis = []
        for a in api_names_list:
            if a not in unique_apis:
                unique_apis.append(a)
        api_names_list = unique_apis
        
        random.shuffle(api_names_list)
        
        for group in ["Group A (Control - Unsplit)", "Group B (Experimental - Split)"]:
            print(f"\n--- Running {group} ---")
            
            # 1. Prepare context APIs in the randomized order
            context_apis_str = []
            
            target_api_desc = None
            for current_api in api_names_list:
                if current_api == target_api:
                    if "Group A" in group:
                        desc = build_api_context(target_api, intent_id=None, tool_desc=tool_desc, intent_defs=intent_defs)
                    else:
                        desc = build_api_context(target_api, intent_id=target_intent_id, tool_desc=tool_desc, intent_defs=intent_defs)
                    target_api_desc = desc
                else:
                    desc = tool_desc[current_api]
                
                context_apis_str.append(f"API_name: {current_api}\nDescription:\n{json.dumps(desc, indent=2, ensure_ascii=False)}")
                
            api_descriptions_full = "\n\n".join(context_apis_str)
            
            prompt_base = prompt_template.format(
                api_descriptions=api_descriptions_full,
                api_names="\n".join(api_names_list)
            )
            
            prompt = prompt_base + "\n\nUser Query: " + query_text
            
            # 2. Call LLM
            messages = [{"role": "system", "content": "You are a helpful assistant."}]
            messages, prompt_tokens = chat_my(messages, prompt, visualize=False, model=MODEL_CKPT, return_tokens=True)
            model_output = messages[-1]["content"]
            
            # 3. Parse Response
            # For parsing we give it the target_api_desc so it can validate
            parsed = parse_response(model_output, api_names_list, json.dumps(target_api_desc), check_API_name=True)
            
            result_entry = {
                "query_id": q["id"],
                "group": group,
                "model_output": model_output,
                "parsed_result": parsed,
                "target_api_desc_used": target_api_desc
            }
            results.append(result_entry)
            
            if parsed["parse_successful"] and parsed["action"] == target_api:
                print(f"✅ Success! Action: {parsed['action']}")
                print(f"Arguments: {parsed['action_input']}")
            else:
                print(f"❌ Failed parsing or wrong API selected: {parsed.get('parse_error_msg', 'Wrong API')}")
                
    # Save results
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\n📦 Saved evaluation results to {RESULTS_PATH}")

if __name__ == "__main__":
    run_test()
