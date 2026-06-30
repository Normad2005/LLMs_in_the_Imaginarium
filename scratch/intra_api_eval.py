import json
import numpy as np
from sentence_transformers import SentenceTransformer

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

print("Loading SentenceTransformer...")
embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

with open('results/intent_definitions.json', 'r', encoding='utf-8') as f:
    intent_defs = json.load(f)

with open('results/improved_hyde_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

# Precompute embeddings for all intents
api_intents = {}
for api_name, api_data in intent_defs.items():
    api_intents[api_name] = []
    for intent in api_data.get("intents", []):
        desc = intent["description"]
        full_text = f"API: {api_name}. Intent: {intent['name']}. Description: {desc}"
        api_intents[api_name].append({
            "intent_id": intent["intent_id"],
            "embedding": embedder.encode(full_text)
        })

intra_api_hits = 0
total = len(results)

print("Calculating Intra-API Accuracy...")
for d in results:
    query = d['query']
    target_api = d['ground_truth_api']
    target_intent_id = d['ground_truth_intent_id']
    hyde_desc = d['hyde_desc']
    
    hyde_emb = embedder.encode(hyde_desc)
    
    best_intent_id = -1
    best_score = -1
    
    for intent in api_intents[target_api]:
        score = cosine_similarity(hyde_emb, intent['embedding'])
        if score > best_score:
            best_score = score
            best_intent_id = intent['intent_id']
            
    if best_intent_id == target_intent_id:
        intra_api_hits += 1
    else:
        print(f"[MISS] Query: {query}")
        print(f"  Target API: {target_api}")
        print(f"  Ground Truth Intent: {target_intent_id}")
        print(f"  Predicted Intent   : {best_intent_id}")
        print(f"  HyDE: {hyde_desc}")
        print("-" * 50)

print(f"\nIntra-API Intent Accuracy: {intra_api_hits}/{total} ({(intra_api_hits/total)*100:.2f}%)")
