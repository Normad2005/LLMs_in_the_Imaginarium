import json

unsplit = json.load(open('results/unsplit_test_results.json', 'r', encoding='utf-8'))
split = json.load(open('results/split_test_results.json', 'r', encoding='utf-8'))
dynamic = json.load(open('results/dynamic_union_test_results.json', 'r', encoding='utf-8'))

apis = list(unsplit.keys())

md_content = "# Final Error Comparison (Unsplit vs Split vs Dynamic Union)\n\n"

for api in apis:
    md_content += f"## API: {api}\n\n"
    
    for i in range(len(unsplit[api])):
        u_item = unsplit[api][i]
        s_item = split[api][i]
        d_item = dynamic[api][i]
        
        u_correct = u_item.get('api_match') == 1 and u_item.get('args_correct') == 1
        s_correct = s_item.get('api_match') == 1 and s_item.get('args_correct') == 1
        d_correct = d_item.get('api_match') == 1 and d_item.get('args_correct') == 1
        
        if u_correct and s_correct and d_correct:
            continue
            
        md_content += f"### Query ID: {u_item['query_id']}\n"
        md_content += f"**Query:** {u_item['query']}\n\n"
        md_content += f"**Ground Truth:**\n```json\n{json.dumps(u_item.get('action_input', {}), indent=2, ensure_ascii=False)}\n```\n\n"
        
        # Unsplit
        if u_correct:
            md_content += "**Unsplit:** ✅ CORRECT\n\n"
        else:
            if u_item.get('api_match') == 0:
                md_content += f"**Unsplit:** ❌ API MISMATCH (Predicted: `{u_item.get('parsed_result', {}).get('action')}`)\n\n"
            else:
                try:
                    pred = json.loads(u_item.get('parsed_result', {}).get('action_input', '{}'))
                    md_content += f"**Unsplit:** ❌ WRONG ARGS\n```json\n{json.dumps(pred, indent=2, ensure_ascii=False)}\n```\n\n"
                except:
                    md_content += f"**Unsplit:** ❌ MALFORMED JSON\n```\n{u_item.get('parsed_result', {}).get('action_input')}\n```\n\n"

        # Split
        if s_correct:
            md_content += "**Split (Golden):** ✅ CORRECT\n\n"
        else:
            if s_item.get('api_match') == 0:
                md_content += f"**Split (Golden):** ❌ API MISMATCH (Predicted: `{s_item.get('parsed_result', {}).get('action')}`)\n\n"
            else:
                try:
                    pred = json.loads(s_item.get('parsed_result', {}).get('action_input', '{}'))
                    md_content += f"**Split (Golden):** ❌ WRONG ARGS\n```json\n{json.dumps(pred, indent=2, ensure_ascii=False)}\n```\n\n"
                except:
                    md_content += f"**Split (Golden):** ❌ MALFORMED JSON\n```\n{s_item.get('parsed_result', {}).get('action_input')}\n```\n\n"
                    
        # Dynamic Union
        if d_correct:
            md_content += "**Dynamic Union:** ✅ CORRECT\n\n"
        else:
            if d_item.get('api_match') == 0:
                md_content += f"**Dynamic Union:** ❌ API MISMATCH (Predicted: `{d_item.get('parsed_result', {}).get('action')}`)\n\n"
            else:
                try:
                    pred = json.loads(d_item.get('parsed_result', {}).get('action_input', '{}'))
                    md_content += f"**Dynamic Union:** ❌ WRONG ARGS\n```json\n{json.dumps(pred, indent=2, ensure_ascii=False)}\n```\n"
                    if d_item.get('intra_intent_hit') == False:
                        md_content += "> ⚠️ *Retrieval failed to find the correct intent within threshold!*\n\n"
                    else:
                        md_content += "\n"
                except:
                    md_content += f"**Dynamic Union:** ❌ MALFORMED JSON\n```\n{d_item.get('parsed_result', {}).get('action_input')}\n```\n\n"
                    
        md_content += "---\n\n"

with open(r'C:\Users\Peter\.gemini\antigravity-ide\brain\d25adce0-0b06-4440-830e-4ce90378ec2d\error_analysis_final.md', 'w', encoding='utf-8') as f:
    f.write(md_content)

print("Generated error_analysis_final.md")
