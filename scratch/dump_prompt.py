import os
import json
import sys

# ensure we can import the module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Exploration.test_unrolled_runner import build_unrolled_apis, BACKGROUND_APIS

def main():
    with open("tool_metadata/tool_description.json", 'r', encoding='utf-8') as f:
        tool_desc = json.load(f)
    with open("results/intent_definitions.json", 'r', encoding='utf-8') as f:
        intent_defs = json.load(f)
    with open("prompts/prompt_template.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()
        
    target_api = "get_hotels_by_location"
    # An example query that failed
    query_text = "I'm planning a family trip to Rome from 2026-10-10 to 2026-10-15. We have 4 adults and need 2 rooms. I've zoomed my map to lat 41.89 to 41.91 and lon 12.48 to 12.50. Show the prices in EUR and descriptions in Italian (it_IT)."
    
    base_api_names_list = list(BACKGROUND_APIS)
    base_api_names_list.append("get_restaurants_by_location")
    base_api_names_list.append(target_api)
    unique_apis = []
    for a in base_api_names_list:
        if a not in unique_apis:
            unique_apis.append(a)
            
    final_api_names_list = []
    context_apis_str = []
    
    for current_api in unique_apis:
        if current_api == target_api:
            unrolled = build_unrolled_apis(target_api, tool_desc, intent_defs)
            for un_name, un_desc in unrolled.items():
                final_api_names_list.append(un_name)
                context_apis_str.append(f"API_name: {un_name}\nDescription:\n{json.dumps(un_desc, indent=2, ensure_ascii=False)}")
        else:
            final_api_names_list.append(current_api)
            context_apis_str.append(f"API_name: {current_api}\nDescription:\n{json.dumps(tool_desc[current_api], indent=2, ensure_ascii=False)}")
            
    api_descriptions_full = "\n\n".join(context_apis_str)
    
    prompt = prompt_template.format(
        api_descriptions=api_descriptions_full,
        api_names="\n".join(final_api_names_list)
    )
    prompt += "\n\nUser Query: " + query_text
    
    with open("unrolled_prompt_dump.md", "w", encoding="utf-8") as f:
        f.write("# 這是傳給小模型的完整 Prompt 範例\n\n```text\n")
        f.write(prompt)
        f.write("\n```\n")

if __name__ == "__main__":
    main()
