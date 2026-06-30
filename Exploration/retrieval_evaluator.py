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

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_hyde_description(query):
    """Uses the SLM to generate a Hypothetical Intent Description based on the user query."""
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
    print("Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("Please install sentence-transformers: pip install sentence-transformers")
        sys.exit(1)
        
    embedder = SentenceTransformer('all-MiniLM-L6-v2')

    print("Loading Data...")
    intent_defs = load_json(INTENT_DEF_PATH)
    queries = load_json(TEST_QUERIES_PATH)
    
    # 1. Flatten all intents and embed them
    all_intents = []
    print("Embedding Intent Descriptions...")
    for api_name, api_data in intent_defs.items():
        for intent in api_data.get("intents", []):
            desc = intent["description"]
            # To give more context to the embedding, we can prepend the API name
            # Or just use the description
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
    
    for idx, q in enumerate(queries):
        query_text = q["query"]
        target_api = q["target_api"]
        target_intent_id = q["target_intent_id"]
        
        print(f"\n[{idx+1}/{total_queries}] Query: {query_text}")
        
        # Step A: HyDE Generation
        hyde_desc = generate_hyde_description(query_text)
        print(f"  HyDE Desc: {hyde_desc[:100]}...")
        
        # Step B: Embedding
        query_emb = embedder.encode([hyde_desc])[0]
        
        # Step C: Compute Similarity
        for intent in all_intents:
            intent["score"] = cosine_similarity(query_emb, intent["embedding"])
            
        # Step D: API-level Max Pooling (Top-1 Intent per API)
        api_best_intents = {}
        for intent in all_intents:
            api = intent["api_name"]
            if api not in api_best_intents or intent["score"] > api_best_intents[api]["score"]:
                api_best_intents[api] = intent
                
        # Step E: Global Sort and Top 10 Selection
        sorted_best_apis = sorted(api_best_intents.values(), key=lambda x: x["score"], reverse=True)
        top10_results = sorted_best_apis[:10]
        
        # Check if ground truth is in Top 10
        found_in_top10 = False
        is_top1 = False
        
        print(f"  Top 3 Retrieved:")
        for r_idx, res in enumerate(top10_results[:3]):
            print(f"    {r_idx+1}. {res['api_name']} (Intent {res['intent_id']}) - Score: {res['score']:.4f}")
            
        for r_idx, res in enumerate(top10_results):
            if res["api_name"] == target_api and res["intent_id"] == target_intent_id:
                found_in_top10 = True
                if r_idx == 0:
                    is_top1 = True
                break
                
        if found_in_top10:
            top10_hits += 1
            if is_top1:
                top1_hits += 1
            print(f"  [HIT] Result: HIT (Top 10)")
        else:
            print(f"  [MISS] Result: MISS")
            # See where it actually ranked
            rank = -1
            for r_idx, res in enumerate(sorted_best_apis):
                if res["api_name"] == target_api and res["intent_id"] == target_intent_id:
                    rank = r_idx + 1
                    break
            print(f"     Ground truth {target_api} (Intent {target_intent_id}) was at rank {rank}")

    print("\n==============================")
    print("EVALUATION RESULTS")
    print(f"Total Queries: {total_queries}")
    print(f"Top-1 Accuracy: {top1_hits}/{total_queries} ({(top1_hits/total_queries)*100:.2f}%)")
    print(f"Top-10 Accuracy (Recall@10): {top10_hits}/{total_queries} ({(top10_hits/total_queries)*100:.2f}%)")
    print("==============================")

if __name__ == "__main__":
    main()
