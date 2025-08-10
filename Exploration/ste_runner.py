# === ste_runner.py ===
import sys
import os
import json
import re
from datetime import datetime
from openai import OpenAI
from datetime import datetime

RUN_ID = datetime.now().strftime("%Y%m%d-%H%M%S")  # 每次啟動一個唯一 run 標識


# 讓 Exploration/ste_runner.py 找得到上層的 real_api.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from real_api import get_weather, get_rain_volume, get_temperature

# ====== 直接寫 API Key ======
OPENAI_API_KEY = "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"  # ← 換成你的真實金鑰
client = OpenAI(api_key=OPENAI_API_KEY)

ALLOWED_APIS = {"get_weather", "get_rain_volume", "get_temperature"}

# ====== API 說明（會放進 prompt）======
api_specs = {
    "get_weather": {
        "description": "Get general weather condition (current).",
        "params": ["location", "date(optional)"]
    },
    "get_rain_volume": {
        "description": "Get rain volume in mm for the last hour.",
        "params": ["location", "date(optional)"]
    },
    "get_temperature": {
        "description": "Get current temperature.",
        "params": ["location", "date(optional)"]
    },
}
api_description_text = "\n".join(
    [f"- {n}: {s['description']}, params: {', '.join(s['params'])}" for n, s in api_specs.items()]
)

# ====== 呼叫 real_api ======
def call_api(api_name, args):
    if "date" in args and (not isinstance(args["date"], str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", args["date"])):
        args.pop("date", None)
    try:
        if api_name == "get_weather":
            return get_weather(**args)
        elif api_name == "get_rain_volume":
            return get_rain_volume(**args)
        elif api_name == "get_temperature":
            return get_temperature(**args)
        else:
            return f"Error: Unknown API '{api_name}'"
    except Exception as e:
        return f"Error: {e}"

# ====== 單次 trial ======
def run_trial(short_term_memory, long_term_memory, episode_id, trial_id):
    memory_snippets = ""
    for m in short_term_memory[-3:]:
        memory_snippets += f"- Q: {m['query']}\n  → Called: {m['api']}({m['args']})\n  → Success: {m['success']}\n"

    long_memory_snippets = ""
    for m in long_term_memory[-5:]:
        long_memory_snippets += f"- Q: {m['query']}\n  → API: {m['api']} → Success: {m['success']}\n"

    prompt = f"""
You are an assistant with access to the following APIs:
{api_description_text}

Only use these APIs: {', '.join(sorted(ALLOWED_APIS))}.
Dates, if provided, should be ISO YYYY-MM-DD; otherwise omit 'date'.

Previous episodes (summary):
{long_memory_snippets if long_memory_snippets else '(no long-term memory yet)'}

Recent trials in this episode:
{memory_snippets if memory_snippets else '(no recent trials yet)'}

Now, imagine a NEW user query that can be answered by a SINGLE call to one API.
Make it natural and not too similar to the above.

User Query:
""".strip()

    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    user_query = resp.choices[0].message.content.strip()

    action_prompt = f"""
User query: "{user_query}"

Pick ONE API and provide arguments in JSON. Use ONLY: {', '.join(sorted(ALLOWED_APIS))}.
If date is not needed, omit it.

{{
  "api_name": "get_weather | get_rain_chance | get_temperature",
  "args": {{"location": "City name" [,"date": "YYYY-MM-DD"]}}
}}
""".strip()

    action_resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": action_prompt}],
        temperature=0.4,
    )

    try:
        action_json = json.loads(action_resp.choices[0].message.content)
        api_name = action_json["api_name"]
        args = action_json.get("args", {})
        if api_name not in ALLOWED_APIS:
            raise ValueError(f"Disallowed API: {api_name}")
        observation = call_api(api_name, args)
    except Exception as e:
        api_name, args = "invalid", {}
        observation = f"Error: {e}"

    reflection_prompt = f"""
You asked: "{user_query}"
You called: {api_name} with args {args}
API returned: "{observation}"

Was this API call appropriate and helpful? Reply only "Yes" or "No".
""".strip()

    refl = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": reflection_prompt}],
        temperature=0,
    )
    is_success = (refl.choices[0].message.content.strip().lower().startswith("yes")
                  and not str(observation).startswith("Error"))
    
    print("Q:", user_query)
    print("Action:", api_name, args)
    print("Observation:", observation)
    print("Success:", is_success)
    print("-" * 60)


    trial = {
        "run_id": RUN_ID,
        "timestamp": datetime.now().isoformat(),
        "episode_id": episode_id,
        "trial_id": trial_id,
        "query": user_query,
        "api": api_name,
        "args": args,
        "observation": observation,
        "success": is_success,
    }
    short_term_memory.append(trial)
    long_term_memory.append(trial)

# ====== 儲存 ======



def _load_existing_trials(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # 如果舊檔破損或非 JSON，就保守起見回傳空陣列避免整個流程掛掉
        return []

def save_trials(new_trials, path="results/ste_trials.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # 讀舊檔 → 合併 → 回存
    existing = _load_existing_trials(path)
    merged = existing + new_trials

    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    # 另外寫一份本次 run 的快照（備查，非必要）
    snapshot = os.path.join(os.path.dirname(path), f"ste_trials_{RUN_ID}.json")
    with open(snapshot, "w", encoding="utf-8") as f:
        json.dump(new_trials, f, indent=2, ensure_ascii=False)

    print(f"✅ Appended {len(new_trials)} trials. Total now: {len(merged)}")
    print(f"📄 Master: {os.path.abspath(path)}")
    print(f"🗂  Snapshot for this run: {os.path.abspath(snapshot)}")

# ====== 入口 ======
if __name__ == "__main__":
    short_term_memory, long_term_memory = [], []
    EPISODES, TRIALS_PER_EPISODE = 1, 5

    for eid in range(1, EPISODES + 1):
        print(f"\n=== Episode {eid} ===")
        short_term_memory.clear()
        for tid in range(1, TRIALS_PER_EPISODE + 1):
            print(f"\n--- Trial {tid} ---")
            run_trial(short_term_memory, long_term_memory, eid, tid)

    save_trials(long_term_memory)
