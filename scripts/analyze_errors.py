import json

def load_results(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

unsplit = load_results('results/unsplit_test_results.json')
split = load_results('results/split_test_results.json')

apis = ['calculate_route', 'get_divisions_near_location']

for api in apis:
    print(f"============================================================")
    print(f"API: {api}")
    print(f"============================================================")
    if api not in unsplit or api not in split:
        continue
        
    for i in range(len(unsplit[api])):
        u_item = unsplit[api][i]
        s_item = split[api][i]
        
        # We only care about errors.
        u_correct = u_item.get('api_match', 0) == 1 and u_item.get('args_correct', 0) == 1
        s_correct = s_item.get('api_match', 0) == 1 and s_item.get('args_correct', 0) == 1
        
        if u_correct and s_correct:
            continue # Both correct, nothing interesting to analyze
            
        print(f"\n[Query ID: {u_item['query_id']}]")
        print(f"Query: {u_item['query']}")
        print(f"Ground Truth : {json.dumps(u_item.get('action_input', {}), ensure_ascii=False)}")
        
        if u_correct:
            print(f"Unsplit      : CORRECT")
        else:
            if u_item.get('api_match', 0) == 0:
                print(f"Unsplit      : API MISMATCH (Predicted: {u_item.get('parsed_result', {}).get('action')})")
            else:
                try:
                    pred_args = json.loads(u_item.get('parsed_result', {}).get('action_input', '{}'))
                    print(f"Unsplit      : WRONG ARGS -> {json.dumps(pred_args, ensure_ascii=False)}")
                except:
                    print(f"Unsplit      : MALFORMED JSON -> {repr(u_item.get('parsed_result', {}).get('action_input'))}")
                    
        if s_correct:
            print(f"Split        : CORRECT")
        else:
            if s_item.get('api_match', 0) == 0:
                print(f"Split        : API MISMATCH (Predicted: {s_item.get('parsed_result', {}).get('action')})")
            else:
                try:
                    pred_args = json.loads(s_item.get('parsed_result', {}).get('action_input', '{}'))
                    print(f"Split        : WRONG ARGS -> {json.dumps(pred_args, ensure_ascii=False)}")
                except:
                    print(f"Split        : MALFORMED JSON -> {repr(s_item.get('parsed_result', {}).get('action_input'))}")
