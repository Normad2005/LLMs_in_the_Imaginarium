import json

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def test_thresholds(hyde_results):
    print("=== Absolute Difference Threshold (s_star - score <= THETA) ===")
    for theta in [0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.1]:
        hits = 0
        total = 0
        total_selected = 0
        for query in hyde_results:
            gt_api = query.get("ground_truth_api")
            gt_intent = query.get("ground_truth_intent_id")
            
            top_apis = query.get("top_k_apis", [])
            for api in top_apis:
                if api["api_name"] == gt_api:
                    all_scores = api["all_intent_scores"]
                    s_star = all_scores[0]["score"]
                    selected = [i for i in all_scores if s_star - i["score"] <= theta]
                    total += 1
                    total_selected += len(selected)
                    if any(i["intent_id"] == gt_intent for i in selected):
                        hits += 1
                    break
        
        recall = 100 * hits / total if total > 0 else 0
        avg_selected = total_selected / total if total > 0 else 0
        print(f"THETA: {theta:<4} | Recall: {recall:5.2f}% | Avg Intents: {avg_selected:.2f}")

    print("\n=== Relative Ratio Threshold (score >= s_star * (1 - THETA)) ===")
    for theta in [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35]:
        hits = 0
        total = 0
        total_selected = 0
        for query in hyde_results:
            gt_api = query.get("ground_truth_api")
            gt_intent = query.get("ground_truth_intent_id")
            
            top_apis = query.get("top_k_apis", [])
            for api in top_apis:
                if api["api_name"] == gt_api:
                    all_scores = api["all_intent_scores"]
                    s_star = all_scores[0]["score"]
                    # If score is negative, relative ratio is tricky, but cosine is usually > 0 here
                    selected = [i for i in all_scores if i["score"] >= s_star * (1 - theta)]
                    total += 1
                    total_selected += len(selected)
                    if any(i["intent_id"] == gt_intent for i in selected):
                        hits += 1
                    break
        
        recall = 100 * hits / total if total > 0 else 0
        avg_selected = total_selected / total if total > 0 else 0
        print(f"Ratio THETA: {theta:<4} | Recall: {recall:5.2f}% | Avg Intents: {avg_selected:.2f}")

if __name__ == '__main__':
    hyde_res = load_json('results/hyde_results_top15_mpnet.json')
    test_thresholds(hyde_res)
