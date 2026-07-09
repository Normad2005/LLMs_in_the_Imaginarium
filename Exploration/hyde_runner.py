import os
import json
import sys
import numpy as np

# Ensure we can import from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Exploration.my_llm import chat_my

# Configuration
TOOL_DESC_PATH = "tool_metadata/tool_description.json"
INTENT_DEF_PATH = "results/intent_definitions.json"
TEST_QUERIES_PATH = "tool_metadata/test_queries_grouped.json"
MODEL_CKPT = "llama3.1:8b-instruct-fp16"
TOP_K = 15  # Number of APIs to retrieve
RESULTS_PATH = f"results/hyde_results_top{TOP_K}.json"

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_hyde_description(query):
    """Uses the SLM to generate a Hypothetical Intent Description based on the user query."""
    prompt = f"""You are a system analyzing a user's query.
User query: "{query}"

Please describe the user's underlying intent in exactly 1 to 2 natural, concise sentences from a first-person perspective.
Do not answer the query. Just describe the intent.

CRITICAL: You MUST include any specific constraints, conditions, or data entities (like locations, currencies, quantities) exactly as provided without generalizing them.
CRITICAL RULE: DO NOT use bullet points, lists, or explicit section headers like "Constraints" or "Parameters". Write it as a seamless first-person thought.
CRITICAL RULE: You MUST write the description entirely in ENGLISH, regardless of the query language. The output must be pure English for semantic matching.
Output ONLY the expanded description, no other text or introductory phrases."""

    messages = [{"role": "system", "content": "You are a helpful assistant that only outputs the requested description."}]
    messages, _ = chat_my(messages, prompt, visualize=False, model=MODEL_CKPT, return_tokens=True)
    return messages[-1]["content"].strip()

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def main():
    print("Loading SentenceTransformer model (all-MiniLM-L6-v2) on CPU...")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Please install sentence-transformers: pip install sentence-transformers")
        sys.exit(1)
        
    embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

    print("Loading Data...")
    intent_defs = load_json(INTENT_DEF_PATH)
    dataset = load_json(TEST_QUERIES_PATH)
    
    # 1. Flatten all intents and embed them
    all_intents = []
    print("Embedding Intent Descriptions...")
    for api_name, api_data in intent_defs.items():
        for intent in api_data.get("intents", []):
            full_text = f"API: {api_name}. Intent: {intent['name']}. Description: {intent['description']}"
            all_intents.append({
                "api_name": api_name,
                "intent_id": intent["intent_id"],
                "intent_data": intent,
                "text": full_text
            })
            
    intent_texts = [i["text"] for i in all_intents]
    intent_embeddings = embedder.encode(intent_texts)
    
    for i, emb in enumerate(intent_embeddings):
        all_intents[i]["embedding"] = emb

    # 2. Evaluate Queries
    global_api_hits = 0
    intra_intent_hits = 0
    total_queries = sum(len(q_list) for q_list in dataset.values())
    
    out_results = []
    evaluated_apis = set()
    
    if os.path.exists(RESULTS_PATH):
        try:
            with open(RESULTS_PATH, 'r', encoding='utf-8') as f:
                out_results = json.load(f)
            # Find which APIs have already been evaluated based on their results
            evaluated_apis = {r.get("ground_truth_api") for r in out_results if "ground_truth_api" in r}
            print(f"Loaded existing results from {RESULTS_PATH}. Will skip {len(evaluated_apis)} already evaluated APIs.")
        except Exception as e:
            print(f"Warning: could not load existing results ({e}). Starting fresh.")
    
    query_idx = 0
    for target_api, queries in dataset.items():
        if target_api in evaluated_apis:
            print(f"Skipping API '{target_api}' (already evaluated)")
            # Need to still advance query_idx so the counter is correct
            query_idx += len(queries)
            continue
            
        for q in queries:
            query_idx += 1
            query_text = q["query"]
            target_intent_id = q["target_intent_id"]
            
            print(f"\n[{query_idx}/{total_queries}] Query: {query_text}")
        
            hyde_desc = generate_hyde_description(query_text)
            print(f"  HyDE Desc: {hyde_desc[:150]}...")
        
            query_emb = embedder.encode([hyde_desc])[0]
        
            # Score all intents
            for intent in all_intents:
                intent["score"] = float(cosine_similarity(query_emb, intent["embedding"]))
            
            # API-level max pooling: for each API, take the highest-scoring intent
            api_best_intents = {}
            for intent in all_intents:
                api = intent["api_name"]
                if api not in api_best_intents or intent["score"] > api_best_intents[api]["score"]:
                    api_best_intents[api] = intent
                
            sorted_best_apis = sorted(api_best_intents.values(), key=lambda x: x["score"], reverse=True)
            top_k_results = sorted_best_apis[:TOP_K]
            top_k_api_names = {r["api_name"] for r in top_k_results}

            # --- Metric 1: Global API Recall@K ---
            # Did target_api appear anywhere in the Top-K retrieved APIs?
            global_api_hit = target_api in top_k_api_names

            # --- Metric 2: Intra-API Intent Recall@1 ---
            # Among target_api's intents, is the highest-scoring one the correct intent?
            intra_intent_hit = False
            if global_api_hit:
                target_api_intents = sorted(
                    [i for i in all_intents if i["api_name"] == target_api],
                    key=lambda x: x["score"],
                    reverse=True
                )
                if target_api_intents and target_api_intents[0]["intent_id"] == target_intent_id:
                    intra_intent_hit = True

            if global_api_hit:
                global_api_hits += 1
            if intra_intent_hit:
                intra_intent_hits += 1

            print(f"  Global API Hit: {global_api_hit} | Intra-Intent Hit: {intra_intent_hit}")

            # Build rich top-K data (for use by test_dynamic_union_runner.py)
            top_k_data = []
            for r in top_k_results:
                api_name = r["api_name"]
                # Collect all intent scores for this API (for Dynamic K thresholding)
                api_intent_scores = sorted(
                    [{"intent_id": i["intent_id"], "score": i["score"], "intent_data": i["intent_data"]}
                     for i in all_intents if i["api_name"] == api_name],
                    key=lambda x: x["score"],
                    reverse=True
                )
                top_k_data.append({
                    "api_name": api_name,
                    "best_intent_id": r["intent_id"],
                    "best_score": r["score"],
                    "all_intent_scores": api_intent_scores
                })

            res_obj = {
                "query_id": q["query_id"],
                "query": query_text,
                "ground_truth_api": target_api,
                "ground_truth_intent_id": target_intent_id,
                "hyde_desc": hyde_desc,
                "top_k_apis": top_k_data,
                "global_api_hit": global_api_hit,
                "intra_intent_hit": intra_intent_hit,
                "result": "HIT" if global_api_hit else "MISS"
            }
            out_results.append(res_obj)

    print(f"\n{'='*50}")
    print(f"RETRIEVAL EVALUATION SUMMARY (Top-{TOP_K})")
    print(f"{'='*50}")
    print(f"Total Queries       : {total_queries}")
    print(f"Global API Recall@{TOP_K} : {global_api_hits}/{total_queries} ({100*global_api_hits/total_queries:.2f}%)")
    print(f"Intra-Intent Recall@1: {intra_intent_hits}/{global_api_hits if global_api_hits else 1} ({100*intra_intent_hits/global_api_hits:.2f}% of API hits)" if global_api_hits else "Intra-Intent Recall@1: N/A")
    print(f"{'='*50}")

    print("\nRetrieval Complete. Saving results...")
    with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(out_results, f, ensure_ascii=False, indent=2)
    print(f"Saved to {RESULTS_PATH}")

if __name__ == "__main__":
    main()
