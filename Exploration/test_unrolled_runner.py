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
    dataset = load_json(TEST_QUERIES_PATH)
    
    with open("prompts/prompt_template.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()
        
    results = {}
    
    print(f"Starting Group D (Unrolled / Virtual APIs) Evaluation with {MODEL_CKPT}...")
    
    for target_api, queries in dataset.items():
        results[target_api] = []
        for q in queries:
            query_text = q["query"]
            target_intent_id = q["target_intent_id"]
            gt_action_input = q["action_input"]
            
            print(f"\n=====================================")
            print(f"Testing Query: {query_text}")
            
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
            target_unrolled_name_prefix = f"{target_api}___"
            
            for current_api in unique_apis:
                if current_api == target_api:
                    unrolled = build_unrolled_apis(target_api, tool_desc, intent_defs)
                    for un_name in unrolled.keys():
                        final_api_names_list.append(un_name)
                else:
                    final_api_names_list.append(current_api)
                    
            random.shuffle(final_api_names_list)
            
            # Build context
            shuffled_context = []
            for a_name in final_api_names_list:
                if a_name.startswith(target_unrolled_name_prefix):
                    unrolled_dict = build_unrolled_apis(target_api, tool_desc, intent_defs)
                    desc = unrolled_dict[a_name]
                else:
                    desc = tool_desc[a_name]
                shuffled_context.append(f"API_name: {a_name}\nDescription:\n{json.dumps(desc, indent=2, ensure_ascii=False)}")
                
            api_descriptions_full = "\n\n".join(shuffled_context)
            target_api_desc = api_descriptions_full # Track for logging
            
            prompt_base = prompt_template.format(
                api_descriptions=api_descriptions_full,
                api_names="\n".join(final_api_names_list)
            )
            prompt = prompt_base + "\n\nUser Query: " + query_text
            
            messages = [{"role": "system", "content": "You are a helpful assistant."}]
            try:
                messages, prompt_tokens = chat_my(messages, prompt, visualize=False, model=MODEL_CKPT, return_tokens=True)
                model_output = messages[-1]["content"]
                
                # Use parse_response to cleanly extract the JSON
                parsed = parse_response(model_output, final_api_names_list, "", check_API_name=True)
                
                result_entry = {
                    "query_id": q["query_id"],
                    "model_output": model_output,
                    "parsed_result": parsed,
                    "target_api_desc_used": target_api_desc,
                    "action_input": gt_action_input,
                    "prompt_tokens": prompt_tokens,
                    "query": query_text
                }
                results[target_api].append(result_entry)
                
                if parsed["parse_successful"] and parsed["action"].startswith(target_api):
                    print(f"✅ Success! Action: {parsed['action']}")
                    print(f"Arguments: {parsed['action_input']}")
                else:
                    print(f"❌ Failed parsing or wrong API selected: {parsed.get('parse_error_msg', 'Wrong API')}")
                    
            except Exception as e:
                print(f"⚠️ ERROR | {e}")
            
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("Evaluation Complete.")

if __name__ == "__main__":
    run_test()
