import json
import re

transcript_path = r"C:\Users\Peter\.gemini\antigravity-ide\brain\77080c88-f555-49df-b7d2-ac31d8539180\.system_generated\logs\transcript.jsonl"

try:
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
            except:
                continue
                
            if data.get("type") == "TOOL_RESPONSE" and "run_command" in data.get("content", ""):
                content = data["content"]
                if "[MISS]" in content:
                    lines = content.split('\n')
                    for i, l in enumerate(lines):
                        if "[MISS]" in l:
                            start = max(0, i-5)
                            end = min(len(lines), i+3)
                            print("\n".join(lines[start:end]))
                            print("-" * 50)
                            
except Exception as e:
    print(e)
