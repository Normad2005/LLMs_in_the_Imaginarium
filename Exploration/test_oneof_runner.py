import os
import json
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Exploration.utils import parse_response
from Exploration.my_llm import chat_my

# Configuration
TOOL_DESC_PATH = "tool_metadata/tool_description.json"
INTENT_DEF_PATH = "results/intent_definitions.json"
TEST_QUERIES_PATH = "tool_metadata/test_queries_grouped.json"
RESULTS_PATH = "results/oneof_test_results.json"
MODEL_CKPT = "llama3.1:8b-instruct-fp16"

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

def build_oneof_api_context(api_name, tool_desc, intent_defs):
    base_schema = tool_desc.get(api_name)
    if not base_schema:
        return {}
        
    if api_name not in intent_defs:
        return base_schema
        
    oneof_list = []
    for intent_data in intent_defs[api_name]["intents"]:
        key_params = intent_data["key_parameters"]
        req_params = []
        opt_params = []
        
        for param in base_schema.get("required_parameters", []):
            if param["name"] in key_params:
                req_params.append(param)
                
        for param in base_schema.get("optional_parameters", []):
            if param["name"] in key_params:
                opt_params.append(param)
                
        oneof_list.append({
            "description": intent_data["description"],
            "required_parameters": req_params,
            "optional_parameters": opt_params
        })
        
    return {
        "description": base_schema.get("description", ""),
        "oneOf": oneof_list
    }

def run_test():
    tool_desc = load_json(TOOL_DESC_PATH)
    intent_defs = load_json(INTENT_DEF_PATH)
    dataset = load_json(TEST_QUERIES_PATH)
    
    with open("prompts/prompt_template.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()
        
    results = {}
    stats = {}

    for target_api, queries in dataset.items():
        results[target_api] = []
        stats[target_api] = {"pass": 0, "fail": 0}
        
        for q in queries:
            query_text = q["query"]
            target_intent_id = q["target_intent_id"]
            gt_action_input = q.get("action_input")
            
            print(f"\n=====================================")
            print(f"Testing Query: {query_text}")
            
            # Determine expected keys based on intent definitions
            target_intent_data = next(i for i in intent_defs[target_api]["intents"] if i["intent_id"] == target_intent_id)
            expected_keys = set(target_intent_data["key_parameters"])
            
            api_names_list = list(BACKGROUND_APIS)
            if target_api == "get_restaurants_by_location":
                api_names_list.append("get_hotels_by_location")
            elif target_api == "get_hotels_by_location":
                api_names_list.append("get_restaurants_by_location")
                
            api_names_list.append(target_api)
            
            unique_apis = []
            for a in api_names_list:
                if a not in unique_apis:
                    unique_apis.append(a)
            api_names_list = unique_apis
            random.shuffle(api_names_list)
            
            context_apis_str = []
            target_api_desc = None
            
            for current_api in api_names_list:
                if current_api == target_api:
                    desc = build_oneof_api_context(target_api, tool_desc, intent_defs)
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
            
            messages = [{"role": "system", "content": "You are a helpful assistant."}]
            try:
                messages, prompt_tokens = chat_my(messages, prompt, visualize=False, model=MODEL_CKPT, return_tokens=True)
                model_output = messages[-1]["content"]
                
                parsed = parse_response(model_output, api_names_list, json.dumps(target_api_desc), check_API_name=True)
                
                result_entry = {
                    "query_id": q.get("id"),
                    "model_output": model_output,
                    "parsed_result": parsed,
                    "target_api_desc_used": target_api_desc,
                    "action_input": gt_action_input,
                    "prompt_tokens": prompt_tokens,
                    "query": query_text
                }
                results[target_api].append(result_entry)
                
                if parsed["parse_successful"] and parsed["action"] == target_api:
                    print(f"✅ Success! Action: {parsed['action']}")
                    print(f"Arguments: {parsed['action_input']}")
                    
                    try:
                        action_input_dict = json.loads(parsed["action_input"])
                        actual_keys = set(action_input_dict.keys())
                        if actual_keys == expected_keys:
                            stats[target_api]["pass"] += 1
                        else:
                            stats[target_api]["fail"] += 1
                    except:
                        stats[target_api]["fail"] += 1
                else:
                    print(f"❌ Failed parsing or wrong API selected: {parsed.get('parse_error_msg', 'Wrong API')}")
                    stats[target_api]["fail"] += 1
                
            except Exception as e:
                stats[target_api]["fail"] += 1
                print(f"⚠️ ERROR | {e}")
                
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n==============================")
    print("GROUP C (oneOf Schema) RESULTS")
    print("==============================")
    total_pass = 0
    total = 0
    for api, counts in stats.items():
        p = counts["pass"]
        f = counts["fail"]
        t = p + f
        total_pass += p
        total += t
        acc = (p / t) * 100 if t > 0 else 0
        print(f"{api:30s} : {p}/{t} ({acc:.1f}%)")
        
    print("-" * 30)
    print(f"TOTAL SCORE: {total_pass}/{total} ({(total_pass/total)*100:.1f}%)")
    print("==============================")

if __name__ == "__main__":
    run_test()
