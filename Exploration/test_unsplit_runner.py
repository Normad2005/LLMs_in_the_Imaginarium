import os
import json
import sys
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Exploration.utils import parse_response
from Exploration.my_llm import chat_my

# Configuration
TEST_TYPE = "complex" # Change to "simple" or "complex"
TOOL_DESC_PATH = "tool_metadata/tool_description.json"
TEST_QUERIES_PATH = f"tool_metadata/test_queries_{TEST_TYPE}.json"
TOP_K = 15
HYDE_RESULTS_PATH = f"results/hyde_results_top{TOP_K}.json"
RESULTS_PATH = f"results/unsplit_test_results_{TEST_TYPE}_top{TOP_K}.json"
MODEL_CKPT = "llama3.1:8b-instruct-fp16"

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_test():
    # Check retrieval results exist
    if not os.path.exists(HYDE_RESULTS_PATH):
        print(f"ERROR: Retrieval results not found at '{HYDE_RESULTS_PATH}'.")
        print("Please run 'Exploration/test_improved_hyde.py' first.")
        sys.exit(1)

    tool_desc = load_json(TOOL_DESC_PATH)
    dataset = load_json(TEST_QUERIES_PATH)
    hyde_results_list = load_json(HYDE_RESULTS_PATH)

    # Build lookup: query_id -> retrieval result
    hyde_lookup = {r["query_id"]: r for r in hyde_results_list}

    with open("prompts/prompt_template.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()

    results = {}
    if os.path.exists(RESULTS_PATH):
        try:
            with open(RESULTS_PATH, "r", encoding="utf-8") as f:
                results = json.load(f)
            print(f"Loaded existing results from {RESULTS_PATH}. Will skip already evaluated queries.")
        except Exception as e:
            print(f"Warning: could not load existing results ({e}). Starting fresh.")

    print(f"Starting Unsplit (Group A) Evaluation with {MODEL_CKPT}...")
    print(f"Using pre-computed HyDE Top-10 from: {HYDE_RESULTS_PATH}\n")

    for target_api, queries in dataset.items():
        if target_api in results and len(results[target_api]) > 0:
            print(f"Skipping API '{target_api}' (already evaluated in results.json)")
            continue
            
        results[target_api] = []

        for q in queries:
            query_id = q["query_id"]
            query_text = q["query"]
            gt_action_input = q["action_input"]

            print(f"\n=====================================")
            print(f"Query ID: {query_id}")
            print(f"Testing Query: {query_text}")

            # Load pre-computed Top-K retrieval results for this query
            if query_id not in hyde_lookup:
                print(f"  WARNING: No retrieval result found for query_id={query_id}, skipping.")
                continue

            retrieval = hyde_lookup[query_id]
            top_k_apis = retrieval["top_k_apis"]

            # Build context: all retrieved APIs use their FULL unsplit schema
            api_names_in_prompt = [entry["api_name"] for entry in top_k_apis]
            context_apis_str = []
            target_api_desc = None

            for entry in top_k_apis:
                api_name = entry["api_name"]
                desc = tool_desc.get(api_name, {})
                if api_name == target_api:
                    target_api_desc = desc
                context_apis_str.append(
                    f"API_name: {api_name}\nDescription:\n{json.dumps(desc, indent=2, ensure_ascii=False)}"
                )

            # Shuffle to avoid position bias
            combined = list(zip(api_names_in_prompt, context_apis_str))
            random.shuffle(combined)
            api_names_in_prompt, context_apis_str = zip(*combined) if combined else ([], [])
            api_names_in_prompt = list(api_names_in_prompt)
            context_apis_str = list(context_apis_str)

            api_descriptions_full = "\n\n".join(context_apis_str)
            prompt_base = prompt_template.format(
                api_descriptions=api_descriptions_full,
                api_names="\n".join(api_names_in_prompt)
            )
            prompt = prompt_base + "\n\nUser Query: " + query_text

            messages = [{"role": "system", "content": "You are a helpful assistant."}]
            messages, prompt_tokens = chat_my(messages, prompt, visualize=False, model=MODEL_CKPT, return_tokens=True)
            model_output = messages[-1]["content"]

            parsed = parse_response(model_output, api_names_in_prompt, json.dumps(target_api_desc), check_API_name=True)

            result_entry = {
                "query_id": query_id,
                "query": query_text,
                "retrieved_apis": api_names_in_prompt,
                "model_output": model_output,
                "parsed_result": parsed,
                "action_input": gt_action_input,
                "prompt_tokens": prompt_tokens,
                "target_api_desc_used": target_api_desc
            }
            results[target_api].append(result_entry)

            if parsed["parse_successful"] and parsed["action"] == target_api:
                print(f"  [HIT] Action: {parsed['action']}")
            else:
                print(f"  [MISS] {parsed.get('parse_error_msg', 'Wrong API or parse failed')}")

    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved evaluation results to {RESULTS_PATH}")

if __name__ == "__main__":
    run_test()
