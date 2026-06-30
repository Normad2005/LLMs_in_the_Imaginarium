import os
import json
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Exploration.utils import parse_response
from Exploration.my_llm import chat_my

TOOL_DESC_PATH = "tool_metadata/tool_description.json"
INTENT_DEF_PATH = "results/intent_definitions.json"
TEST_QUERIES_PATH = "data/test_split_queries.json"
RESULTS_PATH = "results/unrolled_test_results.json"
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

def build_unrolled_apis(api_name, tool_desc, intent_defs):
    base_schema = tool_desc.get(api_name)
    if not base_schema:
        return {}
        
    if api_name not in intent_defs:
        return {api_name: base_schema}
        
    unrolled_apis = {}
    
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
                
        unrolled_name = f"{api_name}___{intent_data['name']}"
        unrolled_apis[unrolled_name] = {
            "description": intent_data["description"],
            "required_parameters": req_params,
            "optional_parameters": opt_params
        }
        
    return unrolled_apis

def run_test():
    tool_desc = load_json(TOOL_DESC_PATH)
    intent_defs = load_json(INTENT_DEF_PATH)
    queries = load_json(TEST_QUERIES_PATH)
    
    with open("prompts/prompt_template.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()
        
    results = []
    
    print(f"Starting Group D (Unrolled / Virtual APIs) Evaluation with {MODEL_CKPT}...")
    
    stats = {
        "calculate_mortgage_payment": {"pass": 0, "fail": 0},
        "get_hotels_by_location": {"pass": 0, "fail": 0},
        "get_restaurants_by_location": {"pass": 0, "fail": 0},
        "get_divisions_near_location": {"pass": 0, "fail": 0}
    }

    for idx, q in enumerate(queries):
        query_text = q["query"]
        target_api = q["target_api"]
        target_intent_id = q["target_intent_id"]
        
        target_intent_data = next(i for i in intent_defs[target_api]["intents"] if i["intent_id"] == target_intent_id)
        expected_keys = set(target_intent_data["key_parameters"])
        
        # Build base background list
        base_api_names_list = list(BACKGROUND_APIS)
        if target_api == "get_restaurants_by_location":
            base_api_names_list.append("get_hotels_by_location")
        elif target_api == "get_hotels_by_location":
            base_api_names_list.append("get_restaurants_by_location")
            
        base_api_names_list.append(target_api)
        
        # Deduplicate
        unique_apis = []
        for a in base_api_names_list:
            if a not in unique_apis:
                unique_apis.append(a)
                
        # Now unroll the target api
        final_api_names_list = []
        context_apis_str = []
        target_unrolled_name_prefix = f"{target_api}___"
        
        for current_api in unique_apis:
            if current_api == target_api:
                unrolled = build_unrolled_apis(target_api, tool_desc, intent_defs)
                for un_name, un_desc in unrolled.items():
                    final_api_names_list.append(un_name)
                    context_apis_str.append(f"API_name: {un_name}\nDescription:\n{json.dumps(un_desc, indent=2, ensure_ascii=False)}")
            else:
                final_api_names_list.append(current_api)
                context_apis_str.append(f"API_name: {current_api}\nDescription:\n{json.dumps(tool_desc[current_api], indent=2, ensure_ascii=False)}")
                
        random.shuffle(final_api_names_list)
        
        # We must rebuild context_apis_str to match the shuffled order
        shuffled_context = []
        for a_name in final_api_names_list:
            if a_name.startswith(target_unrolled_name_prefix):
                unrolled_dict = build_unrolled_apis(target_api, tool_desc, intent_defs)
                desc = unrolled_dict[a_name]
            else:
                desc = tool_desc[a_name]
            shuffled_context.append(f"API_name: {a_name}\nDescription:\n{json.dumps(desc, indent=2, ensure_ascii=False)}")
            
        api_descriptions_full = "\n\n".join(shuffled_context)
        
        prompt_base = prompt_template.format(
            api_descriptions=api_descriptions_full,
            api_names="\n".join(final_api_names_list)
        )
        prompt = prompt_base + "\n\nUser Query: " + query_text
        
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        try:
            messages, _ = chat_my(messages, prompt, visualize=False, model=MODEL_CKPT, return_tokens=True)
            model_output = messages[-1]["content"]
            
            # Use parse_response to cleanly extract the JSON
            parsed = parse_response(model_output, final_api_names_list, "", check_API_name=True)
            
            passed = False
            error_reason = ""
            
            if parsed["parse_successful"] and parsed["action"].startswith(target_unrolled_name_prefix):
                # The LLM selected one of our virtual APIs!
                try:
                    action_input_dict = json.loads(parsed["action_input"])
                    actual_keys = set(action_input_dict.keys())
                    
                    if actual_keys == expected_keys:
                        passed = True
                    else:
                        error_reason = f"Mismatch. Missing: {expected_keys - actual_keys}, Extra: {actual_keys - expected_keys}"
                except json.JSONDecodeError:
                    error_reason = "Invalid JSON in action_input"
            else:
                error_reason = f"Parse failed or wrong API: {parsed.get('parse_error_msg', parsed.get('action'))}"
                
            if passed:
                stats[target_api]["pass"] += 1
                print(f"[{idx+1}/60] ✅ PASS | {target_api} (via {parsed.get('action')})")
            else:
                stats[target_api]["fail"] += 1
                print(f"[{idx+1}/60] ❌ FAIL | {target_api} | {error_reason}")
                
            results.append({
                "query_id": q["id"],
                "group": "Group D (Unrolled)",
                "passed": passed,
                "error": error_reason,
                "model_output": model_output
            })
            
        except Exception as e:
            stats[target_api]["fail"] += 1
            print(f"[{idx+1}/60] ⚠️ ERROR | {e}")
            
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n==============================")
    print("GROUP D (Unrolled Schema) RESULTS")
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
