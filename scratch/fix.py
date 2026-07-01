import json

with open('tool_metadata/tool_test.json', 'r', encoding='utf-8') as f:
    tool_test = json.load(f)

# build lookup
lookup = {}
for api, queries in tool_test.items():
    for q in queries:
        lookup[q['query']] = q.get('action_input', {})

with open('tool_metadata/test_queries_grouped.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)

updated_count = 0
for api, queries in dataset.items():
    for q in queries:
        text = q['query']
        if text in lookup:
            q['action_input'] = lookup[text]
            updated_count += 1
        else:
            print('Warning: Query not found:', text)

with open('tool_metadata/test_queries_grouped.json', 'w', encoding='utf-8') as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)

print('Successfully updated ' + str(updated_count) + ' queries with action_input.')

# Also check dynamic K merges
with open('results/improved_hyde_results.json', 'r', encoding='utf-8') as f:
    hyde = json.load(f)

print('\n=== Dynamic K Merge Stats (THETA=0.05) ===')
merged_count = 0
for item in hyde:
    top_api = item['top_k_apis'][0]
    all_scores = top_api['all_intent_scores']
    s_star = all_scores[0]['score']
    selected = [x for x in all_scores if (s_star - x['score']) <= 0.05]
    if len(selected) > 1:
        merged_count += 1
        intents = [x['intent_data']['intent_id'] for x in selected]
        print(f"  [{item['query_id']}] API: {top_api['api_name']} merged {len(selected)} intents: {intents}")

print('Total queries with 2+ intents merged:', merged_count)
