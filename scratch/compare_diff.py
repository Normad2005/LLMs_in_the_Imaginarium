import json

with open('results/split_test_results.json', 'r', encoding='utf-8') as f:
    split_res = json.load(f)

with open('results/dynamic_union_test_results.json', 'r', encoding='utf-8') as f:
    dyn_res = json.load(f)

with open('tool_metadata/test_queries_grouped.json', 'r', encoding='utf-8') as f:
    dataset = json.load(f)
gt_map = {}
for api, queries in dataset.items():
    for q in queries:
        gt_map[q['query_id']] = q['action_input']

def get_args_correct(parsed, gt_action_input, gt_api):
    if not parsed['parse_successful'] or parsed.get('action') != gt_api:
        return False
    try:
        model_dict = json.loads(parsed['action_input'])
    except:
        return False
    
    for k, v in gt_action_input.items():
        if k not in model_dict or str(model_dict[k]).strip().lower() != str(v).strip().lower():
            return False
    return True

print('=== Split Correct, Dynamic Union Wrong ===')
diff_count = 0
for api in split_res:
    for s_item, d_item in zip(split_res[api], dyn_res[api]):
        q_id = s_item['query_id']
        gt = gt_map[q_id]
        
        s_corr = get_args_correct(s_item['parsed_result'], gt, api)
        d_corr = get_args_correct(d_item['parsed_result'], gt, api)
        
        if s_corr and not d_corr:
            diff_count += 1
            print(f'\n[Query ID: {q_id}] API: {api}')
            print(f'Query: {s_item["query"]}')
            print(f'Ground Truth: {json.dumps(gt)}')
            try:
                print(f'Split output: {json.loads(s_item["parsed_result"]["action_input"])}')
            except: pass
            try:
                print(f'Dynamic output: {json.loads(d_item["parsed_result"]["action_input"])}')
            except: pass
            print(f"Split API hit: {s_item['parsed_result']['action']}")
            print(f"Dyn API hit: {d_item['parsed_result']['action']}")

print(f'\nTotal differences where Split is correct and Dynamic Union is wrong: {diff_count}')
