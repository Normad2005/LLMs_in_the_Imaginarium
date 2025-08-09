# ste_runner.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from openai import OpenAI
import random
import json
from datetime import datetime
from collections import defaultdict
from mock_api import get_weather, get_rain_chance, get_temperature




# 初始化 OpenAI API
client = OpenAI(api_key="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")

# 模擬 API spec
api_specs = {
    "get_weather": {"description": "Returns general weather info", "params": ["location", "date"]},
    "get_rain_chance": {"description": "Returns the chance of rain", "params": ["location", "date"]},
    "get_temperature": {"description": "Returns the temperature range", "params": ["location", "date"]},
}

# 顯示給模型的 API 說明
api_description_text = "\n".join([
    f"- {name}: {spec['description']}, params: {', '.join(spec['params'])}"
    for name, spec in api_specs.items()
])

# 模擬 API 呼叫
def call_api(api_name, args):
    try:
        if api_name == "get_weather":
            return get_weather(**args)
        elif api_name == "get_rain_chance":
            return get_rain_chance(**args)
        elif api_name == "get_temperature":
            return get_temperature(**args)
        else:
            return f"Error: Unknown API '{api_name}'"
    except Exception as e:
        return f"Error: {e}"

# 執行一個 trial
def run_trial(short_term_memory, long_term_memory, episode_id, trial_id):
    # 取過去所有成功或失敗的 trial 概要（long-term memory）
    long_memory_snippets = ""
    for m in long_term_memory[-10:]:  # 最多顯示 10 筆
        long_memory_snippets += f"- Q: {m['query']}\n  → API: {m['api']} → Success: {m['success']}\n"
    # 讓模型想像 user query
    prompt = f"""
It is 2025. You are an assistant with access to the following APIs:
{api_description_text}

Now, imagine a realistic user query that could be answered by calling ONE of the APIs.
Avoid repeating previous queries. Here are some past examples:
{[m['query'] for m in long_term_memory[-5:]]}

User Query:
""".strip()

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    user_query = response.choices[0].message.content.strip()
    print(f"\n🤔 Imagined Query: {user_query}")

    # 讓模型選擇 API 與參數
    action_prompt = f"""
User query: "{user_query}"

Now decide:
1) which API to call (from: {list(api_specs.keys())})
2) provide values for 'location' and 'date' (e.g., YYYY-MM-DD)

Use the following JSON format:
{{
  "api_name": "...",
  "args": {{
    "location": "...",
    "date": "YYYY-MM-DD"
  }}
}}
""".strip()

    action_response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": action_prompt}],
        temperature=0.7
    )

    try:
        action_json = json.loads(action_response.choices[0].message.content)
        api_name = action_json["api_name"]
        args = action_json["args"]
        observation = call_api(api_name, args)
    except Exception as e:
        print("❌ Failed to parse or call API:", e)
        api_name = "invalid"
        args = {}
        observation = f"Error: {e}"

    print(f"🛠️ API called: {api_name} with args {args}")
    print(f"📡 Observation: {observation}")

    # 模型自我反思
    reflection_prompt = f"""
Here is the user query: "{user_query}"
You chose to call: {api_name}({args})
The API returned: "{observation}"

Do you think this API call was helpful and relevant to answer the query?
Respond only "Yes" or "No".
""".strip()

    reflection_response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": reflection_prompt}],
        temperature=0
    )

    reflection_text = reflection_response.choices[0].message.content.strip().lower()
    is_success = reflection_text.startswith("yes") and not observation.startswith("Error")

    print(f"🪞 Self-reflection: {'✅ Successful' if is_success else '❌ Unsuccessful'}")

    # 記錄 trial
    trial = {
        "timestamp": datetime.now().isoformat(),
        "episode_id": episode_id,
        "trial_id": trial_id,
        "query": user_query,
        "api": api_name,
        "args": args,
        "observation": observation,
        "success": is_success
    }

    short_term_memory.append(trial)
    long_term_memory.append(trial)

# 儲存結果到 json
def save_trials(trials):
    os.makedirs("results", exist_ok=True)
    with open("results/ste_trials.json", "w", encoding="utf-8") as f:
        json.dump(trials, f, indent=2, ensure_ascii=False)

    # 依 API 分類
    per_api = defaultdict(list)
    for t in trials:
        per_api[t["api"]].append(t)

    os.makedirs("results/by_api", exist_ok=True)
    for api, trials in per_api.items():
        path = f"results/by_api/{api}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(trials, f, indent=2, ensure_ascii=False)

    print("✅ Trials saved to results/")

# ==== 主程式執行 ====
short_term_memory = []
long_term_memory = []

EPISODES = 3
TRIALS_PER_EPISODE = 5

for episode_id in range(1, EPISODES + 1):
    print(f"\n=== 🌟 Episode {episode_id} ===")
    short_term_memory.clear()
    for trial_id in range(1, TRIALS_PER_EPISODE + 1):
        print(f"\n--- Trial {trial_id} ---")
        run_trial(short_term_memory, long_term_memory, episode_id, trial_id)

save_trials(long_term_memory)
