import json

with open('results/unsplit_test_results.json', 'r', encoding='utf-8') as f:
    unsplit = json.load(f)
with open('results/split_test_results.json', 'r', encoding='utf-8') as f:
    split = json.load(f)

apis = ['get_planet_data', 'get_flights_in_bounding_box']
for api in apis:
    print(f"=== {api} ===")
    for i in range(len(unsplit[api])):
        u_item = unsplit[api][i]
        s_item = split[api][i]
        s_correct = s_item.get('api_match') == 1 and s_item.get('args_correct') == 1
        if not s_correct:
            print(f"Query: {s_item['query']}")
            print(f"GT: {u_item.get('action_input')}")
            print(f"Pred: {s_item.get('parsed_result', {}).get('action_input')}")
