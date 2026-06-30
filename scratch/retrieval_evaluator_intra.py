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
    print("Loading SentenceTransformer model...")
    from sentence_transformers import SentenceTransformer
    embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

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

    intra_api_hits = 0
    top1_hits = 0
    total_queries = len(queries)
    
    for idx, q in enumerate(queries):
        query_text = q["query"]
        target_api = q["target_api"]
        target_intent_id = q["target_intent_id"]
        
        hyde_desc = generate_hyde_description(query_text)
        query_emb = embedder.encode([hyde_desc])[0]
        
        # Intra-API calculation
        best_intent_id = -1
        best_score = -1
        
        for intent in all_intents:
            if intent["api_name"] == target_api:
                score = float(cosine_similarity(query_emb, intent["embedding"]))
                if score > best_score:
                    best_score = score
                    best_intent_id = intent["intent_id"]
                    
        if best_intent_id == target_intent_id:
            intra_api_hits += 1
        else:
            print(f"[MISS] Query: {query_text}")
            print(f"       HyDE: {hyde_desc}")

        # Global Top-1 calculation (to reproduce the 85-88%)
        api_best_intents = {}
        for intent in all_intents:
            intent["score"] = float(cosine_similarity(query_emb, intent["embedding"]))
            api = intent["api_name"]
            if api not in api_best_intents or intent["score"] > api_best_intents[api]["score"]:
                api_best_intents[api] = intent
        sorted_best_apis = sorted(api_best_intents.values(), key=lambda x: x["score"], reverse=True)
        top1 = sorted_best_apis[0]
        if top1["api_name"] == target_api and top1["intent_id"] == target_intent_id:
            top1_hits += 1

    print("\n==============================")
    print("ORIGINAL BASELINE EVALUATION RESULTS")
    print(f"Total Queries: {total_queries}")
    print(f"Global Top-1 Accuracy: {top1_hits}/{total_queries} ({(top1_hits/total_queries)*100:.2f}%)")
    print(f"Intra-API Accuracy: {intra_api_hits}/{total_queries} ({(intra_api_hits/total_queries)*100:.2f}%)")
    print("==============================")

if __name__ == "__main__":
    main()
