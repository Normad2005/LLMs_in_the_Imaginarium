import json
split = json.load(open('results/split_test_results.json', 'r', encoding='utf-8'))
for q in split['get_divisions_near_location']:
    if not (q.get('api_match') == 1 and q.get('args_correct') == 1):
        print(f"GT: {q.get('action_input')}")
        print(f"PD: {q.get('parsed_result', {}).get('action_input')}")
        print("---")
