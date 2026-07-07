import json

# 1. Update tool_test.json for calculate_route
with open('tool_metadata/tool_test.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

for q in d['calculate_route']:
    query = q['query'].lower()
    ai = q['action_input']
    
    # Remove default voice_instructions (if it's "0")
    if ai.get('voice_instructions') == '0':
        del ai['voice_instructions']
        
    # Remove default finish_instruction (if it's "0")
    if ai.get('finish_instruction') == '0':
        del ai['finish_instruction']
        
    # Remove default format (if it's "json" and not explicitly asked)
    if ai.get('format') == 'json' and 'json' not in query:
        del ai['format']
        
    # Remove default language (if it's "en" and not explicitly asked)
    if ai.get('language') == 'en' and 'english' not in query and ' en' not in query:
        del ai['language']

with open('tool_metadata/tool_test.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)


# 2. Update tool_description.json for get_divisions_near_location
with open('tool_metadata/tool_description.json', 'r', encoding='utf-8') as f:
    d2 = json.load(f)

for param in d2['get_divisions_near_location']['required_parameters']:
    if param['name'] == 'locationId':
        # Replace the description
        param['description'] = "The GPS coordinate of the center location, must follow ISO-6709 format (e.g. +34.05+118.24 or +34.05-118.24) where + denotes North/East and - denotes South/West."

with open('tool_metadata/tool_description.json', 'w', encoding='utf-8') as f:
    json.dump(d2, f, indent=2, ensure_ascii=False)
