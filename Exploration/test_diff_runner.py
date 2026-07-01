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
RESULTS_PATH = "results/diff_test_results.json"
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

def build_diff_api_context(api_name, tool_desc, intent_defs):
    base_schema = tool_desc.get(api_name)
    if not base_schema:
        return ""
        
    if api_name not in intent_defs:
        return json.dumps(base_schema, indent=2, ensure_ascii=False)
        
    intents = intent_defs[api_name]["intents"]
    if not intents:
        return json.dumps(base_schema, indent=2, ensure_ascii=False)
        
    common_params_names = set(intents[0]["key_parameters"])
    for intent in intents[1:]:
        common_params_names = common_params_names.intersection(set(intent["key_parameters"]))
        
    param_map = {}
    for p in base_schema.get("required_parameters", []):
        param_map[p["name"]] = {"desc": p["description"], "type": p["type"], "required": True}
    for p in base_schema.get("optional_parameters", []):
        param_map[p["name"]] = {"desc": p["description"], "type": p["type"], "required": False}
        
    text_lines = []
    text_lines.append(f"{base_schema.get('description', '')}")
    text_lines.append("")
    text_lines.append("[COMMON PARAMETERS] - These are always required/available regardless of the intent.")
    for p_name in common_params_names:
        p_info = param_map.get(p_name)
        if p_info:
            req_str = "required" if p_info["required"] else "optional"
            text_lines.append(f"- {p_name} ({p_info['type']}, {req_str}): {p_info['desc']}")
            
    text_lines.append("")
    text_lines.append("[INTENT OPTIONS] - Choose EXACTLY ONE intent based on the user's query. In your Action Input, you must include the COMMON PARAMETERS plus the Specific Parameters of your chosen intent.")
    
    for intent in intents:
        text_lines.append("")
        text_lines.append(f"Intent Name: {intent['name']}")
        text_lines.append(f"Description: {intent['description']}")
        
        specific_params = set(intent["key_parameters"]) - common_params_names
        if specific_params:
            text_lines.append("Specific Parameters for this intent:")
            for p_name in specific_params:
                p_info = param_map.get(p_name)
                if p_info:
                    req_str = "required" if p_info["required"] else "optional"
                    text_lines.append(f"  - {p_name} ({p_info['type']}, {req_str}): {p_info['desc']}")
        else:
            text_lines.append("Specific Parameters for this intent: None")
            
    return "\n".join(text_lines)

def run_test():
    tool_desc = load_json(TOOL_DESC_PATH)
    intent_defs = load_json(INTENT_DEF_PATH)
    dataset = load_json(TEST_QUERIES_PATH)
    
    with open("prompts/prompt_template.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()
        
    results = {}
    
    import random

    for target_api, queries in dataset.items():
        results[target_api] = []
        for q in queries:
            query_text = q["query"]
            target_intent_id = q["target_intent_id"]
            gt_action_input = q["action_input"]
            
            print(f"\n=====================================")
            print(f"Testing Query: {query_text}")
            
            api_names_list = list(BACKGROUND_APIS)
            if target_api not in api_names_list:
                api_names_list.append(target_api)
                
            random.shuffle(api_names_list)
            
            context_apis_str = []
            target_api_desc = ""
            
            for current_api in api_names_list:
                if current_api == target_api:
                    target_api_desc = build_diff_api_context(target_api, tool_desc, intent_defs)
                    context_apis_str.append(f"API_name: {current_api}\nDescription:\n{target_api_desc}")
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
                
                parsed = parse_response(model_output, api_names_list, "", check_API_name=True)
                
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
                
                if parsed["parse_successful"] and parsed["action"] == target_api:
                    print(f"✅ Success! Action: {parsed['action']}")
                    print(f"Arguments: {parsed['action_input']}")
                else:
                    print(f"❌ Failed parsing or wrong API selected: {parsed.get('parse_error_msg', 'Wrong API')}")
                    
            except Exception as e:
                print(f"⚠️ ERROR | {e}")
            
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print("\n==============================")
    print("Evaluation Complete.")

if __name__ == "__main__":
    run_test()
