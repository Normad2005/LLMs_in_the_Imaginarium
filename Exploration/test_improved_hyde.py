import os
import json
import sys
import numpy as np

# Ensure we can import from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Exploration.my_llm import chat_my

# Configuration
INTENT_DEF_PATH = "results/intent_definitions.json"
TEST_QUERIES_PATH = "data/test_split_queries.json"
MODEL_CKPT = "llama3.1:8b-instruct-fp16"
OUTPUT_PATH = "results/improved_hyde_results.json"

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
    queries = load_json(TEST_QUERIES_PATH)
    
    # 1. Flatten all intents and embed them
    all_intents = []
    print("Embedding Intent Descriptions...")
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

    # 2. Evaluate Queries
    top10_hits = 0
    top1_hits = 0
    total_queries = len(queries)
    
    out_results = []
    
    for idx, q in enumerate(queries):
        query_text = q["query"]
        target_api = q["target_api"]
        target_intent_id = q["target_intent_id"]
        
        print(f"\n[{idx+1}/{total_queries}] Query: {query_text}")
        
        hyde_desc = generate_hyde_description(query_text)
        print(f"  HyDE Desc: {hyde_desc[:150]}...")
        
        query_emb = embedder.encode([hyde_desc])[0]
        
        for intent in all_intents:
            intent["score"] = float(cosine_similarity(query_emb, intent["embedding"]))
            
        api_best_intents = {}
        for intent in all_intents:
            api = intent["api_name"]
            if api not in api_best_intents or intent["score"] > api_best_intents[api]["score"]:
                api_best_intents[api] = intent
                
        sorted_best_apis = sorted(api_best_intents.values(), key=lambda x: x["score"], reverse=True)
        top10_results = sorted_best_apis[:10]
        
        found_in_top10 = False
        is_top1 = False
        
        for r_idx, res in enumerate(top10_results):
            if res["api_name"] == target_api and res["intent_id"] == target_intent_id:
                found_in_top10 = True
                if r_idx == 0:
                    is_top1 = True
                break
                
        res_obj = {
            "query": query_text,
            "ground_truth_api": target_api,
            "ground_truth_intent_id": target_intent_id,
            "hyde_desc": hyde_desc,
            "top_3": [
                {"api_name": r["api_name"], "intent_id": r["intent_id"], "score": r["score"]} for r in top10_results[:3]
            ],
            "result": "HIT" if found_in_top10 else "MISS"
        }
        out_results.append(res_obj)
        
        if found_in_top10:
            top10_hits += 1
            if is_top1:
                top1_hits += 1
            print(f"  [HIT] Top-1: {is_top1}")
        else:
            print(f"  [MISS]")

    print("\n==============================")
    print("IMPROVED HYDE EVALUATION RESULTS")
    print(f"Total Queries: {total_queries}")
    print(f"Top-1 Accuracy: {top1_hits}/{total_queries} ({(top1_hits/total_queries)*100:.2f}%)")
    print(f"Top-10 Accuracy: {top10_hits}/{total_queries} ({(top10_hits/total_queries)*100:.2f}%)")
    print("==============================")
    
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(out_results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
