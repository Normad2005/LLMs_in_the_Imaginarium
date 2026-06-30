import json
with open('results/improved_hyde_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print('=== TOP-1 MISSES ===\n')
count = 0
for d in data:
    top1 = d['top_3'][0]
    if top1['api_name'] != d['ground_truth_api'] or top1['intent_id'] != d['ground_truth_intent_id']:
        count += 1
        print(f"[{count}] Query: {d['query']}")
        print(f"    Ground Truth: {d['ground_truth_api']} (Intent {d['ground_truth_intent_id']})")
        print(f"    Top-1 Pred  : {top1['api_name']} (Intent {top1['intent_id']}) Score: {top1['score']:.4f}")
        print(f"    HyDE Desc   : {d['hyde_desc']}")
        print('-'*80)
