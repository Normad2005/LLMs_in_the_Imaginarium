import json

with open('tool_metadata/tool_test.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# 1. calculate_route: boolean strings to 1/0
for q in d['calculate_route']:
    if 'voice_instructions' in q['action_input']:
        if q['action_input']['voice_instructions'] == 'true':
            q['action_input']['voice_instructions'] = '1'
        elif q['action_input']['voice_instructions'] == 'false':
            q['action_input']['voice_instructions'] = '0'
    if 'finish_instruction' in q['action_input']:
        if q['action_input']['finish_instruction'] == 'true':
            q['action_input']['finish_instruction'] = '1'
        elif q['action_input']['finish_instruction'] == 'false':
            q['action_input']['finish_instruction'] = '0'

# 2. get_divisions_near_location: sort direction
for q in d['get_divisions_near_location']:
    if q['query'] == "I'm planning a road trip around coordinates 34.05, -118.24. I want to visit large US cities within a 50-mile radius that have over 50,000 residents. Can you list them sorted by distance?":
        q['query'] = "I'm planning a road trip around coordinates 34.05, -118.24. I want to visit large US cities within a 50-mile radius that have over 50,000 residents. Can you list them sorted by distance, from closest to farthest?"
    elif q['query'] == "Find places near 51.50, -0.12 within 15 miles. Sort by distance.":
        q['query'] = "Find places near 51.50, -0.12 within 15 miles. Sort by distance, from closest to farthest."

# 3. get_flights_in_bounding_box: remove limit if not explicitly requested
for q in d['get_flights_in_bounding_box']:
    if 'limit' in q['action_input']:
        limit_val = q['action_input']['limit']
        if str(limit_val) not in q['query']:
            # The number is not in the query, meaning it was defaulted.
            del q['action_input']['limit']

with open('tool_metadata/tool_test.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
