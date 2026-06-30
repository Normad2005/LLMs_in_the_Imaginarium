import json
import numpy as np
from sentence_transformers import SentenceTransformer

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')

with open('results/intent_definitions.json', 'r', encoding='utf-8') as f:
    intent_defs = json.load(f)

with open('results/improved_hyde_results.json', 'r', encoding='utf-8') as f:
    results = json.load(f)

api_intents = {}
for api_name, api_data in intent_defs.items():
    api_intents[api_name] = []
    for intent in api_data.get("intents", []):
        full_text = f"API: {api_name}. Intent: {intent['name']}. Description: {intent['description']}"
        api_intents[api_name].append({
            "intent_id": intent["intent_id"],
            "name": intent['name'],
            "embedding": embedder.encode(full_text)
        })

for d in results:
    target_api = d['ground_truth_api']
    target_intent_id = d['ground_truth_intent_id']
    hyde_desc = d['hyde_desc']
    hyde_emb = embedder.encode(hyde_desc)
    
    best_intent_id = -1
    best_score = -1
    target_score = -1
    
    for intent in api_intents[target_api]:
        score = float(cosine_similarity(hyde_emb, intent['embedding']))
        if score > best_score:
            best_score = score
            best_intent_id = intent['intent_id']
        if intent['intent_id'] == target_intent_id:
            target_score = score
            
    if best_intent_id != target_intent_id:
        theta = best_score - target_score
        print(f"Query: {d['query']}")
        print(f"  Target API: {target_api}")
        print(f"  Ground Truth Intent: {target_intent_id} (Score: {target_score:.4f})")
        print(f"  Predicted Intent   : {best_intent_id} (Score: {best_score:.4f})")
        print(f"  Gap (Theta) Needed : {theta:.4f}")
        print("-" * 50)
