import os
import json
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Exploration.my_llm import chat_my

INTENT_DEF_PATH = "results/intent_definitions.json"
TEST_QUERIES_PATH = "data/test_split_queries.json"
MODEL_CKPT = "llama3.1:8b-instruct-fp16"

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_hyde_description(query):
    prompt = f"""You are a system analyzing a user's query.
User query: "{query}"

Please expand this query by describing the user's underlying intent, their goal, and the parameters they might need to provide, written in a first-person perspective.
Do not answer the query. Just describe the intent.
CRITICAL RULE: You MUST write the expanded description entirely in ENGLISH, regardless of what language the user asks for in the results or uses in the query. The output must be pure English for semantic matching purposes.
Output ONLY the expanded description, no other text or introductory phrases."""

    messages = [{"role": "system", "content": "You are a helpful assistant that only outputs the requested description."}]
    messages, _ = chat_my(messages, prompt, visualize=False, model=MODEL_CKPT, return_tokens=True)
    return messages[-1]["content"].strip()

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def main():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Please install sentence-transformers")
        sys.exit(1)
        
    embedder = SentenceTransformer('all-MiniLM-L6-v2')

    intent_defs = load_json(INTENT_DEF_PATH)
    queries = load_json(TEST_QUERIES_PATH)
    
    all_intents = []
    for api_name, api_data in intent_defs.items():
        for intent in api_data.get("intents", []):
            desc = intent["description"]
            full_text = f"API: {api_name}. Intent: {intent['name']}. Description: {desc}"
            all_intents.append({
                "api_name": api_name,
                "intent_id": intent["intent_id"],
                "text": full_text
            })
            
    intent_texts = [i["text"] for i in all_intents]
    intent_embeddings = embedder.encode(intent_texts)
    
    for i, emb in enumerate(intent_embeddings):
        all_intents[i]["embedding"] = emb

    results_data = []
    
    print("Running Dense Retrieval and computing similarities...")
    
    for idx, q in enumerate(queries):
        query_text = q["query"]
        target_api = q["target_api"]
        target_intent_id = q["target_intent_id"]
        
        hyde_desc = generate_hyde_description(query_text)
        query_emb = embedder.encode([hyde_desc])[0]
        
        api_intents = [i for i in all_intents if i["api_name"] == target_api]
        if len(api_intents) <= 1:
            continue
            
        for intent in api_intents:
            intent["score"] = float(cosine_similarity(query_emb, intent["embedding"]))
            
        api_intents = sorted(api_intents, key=lambda x: x["score"], reverse=True)
        best_intent = api_intents[0]
        S_star = best_intent["score"]
        
        gt_intent = next((i for i in api_intents if i["intent_id"] == target_intent_id), None)
        gt_score = gt_intent["score"] if gt_intent else 0
        rel_diff_gt = (S_star - gt_score) / S_star if S_star > 0 else 0
        
        all_rel_diffs = [(S_star - i["score"])/S_star for i in api_intents[1:]]
        
        results_data.append({
            "query_idx": idx,
            "top1_missed": best_intent["intent_id"] != target_intent_id,
            "rel_diff_gt": rel_diff_gt,
            "all_rel_diffs": all_rel_diffs
        })
        
    print("\n--- THETA ANALYSIS ---")
    thetas_to_test = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.15]
    total_multi_queries = len(results_data)
    total_missed = sum(1 for r in results_data if r["top1_missed"])
    
    print(f"Total Multi-Intent Queries: {total_multi_queries}")
    print(f"Top-1 Missed Correct Intent: {total_missed}")
    
    print("\nTheta | Rescued / Missed | False Positives (Extra intents pulled when Top-1 was already right)")
    print("-" * 80)
    for t in thetas_to_test:
        rescued = sum(1 for r in results_data if r["top1_missed"] and r["rel_diff_gt"] <= t)
        false_positives = 0
        for r in results_data:
            if not r["top1_missed"]:
                extra_pulled = sum(1 for diff in r["all_rel_diffs"] if diff <= t)
                false_positives += extra_pulled
        print(f"{t:5.2f} | {rescued:7d} / {total_missed:<6d} | {false_positives}")
        
    print("\n[Details of Missed Queries (Rel Diff needed to rescue)]")
    for r in results_data:
        if r["top1_missed"]:
            print(f"Query {r['query_idx']+1}: Rel Diff = {r['rel_diff_gt']:.4f}")

if __name__ == "__main__":
    main()
