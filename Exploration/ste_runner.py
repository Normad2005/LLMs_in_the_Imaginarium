# === ste_runner.py ===
import sys
import os
import json
import re
from datetime import datetime
#from openai import OpenAI
import requests

RUN_ID = datetime.now().strftime("%Y%m%d-%H%M%S")  # 每次啟動一個唯一 run 標識

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from real_api import get_current_weather, get_current_temperature, get_forecast, get_wikipedia_summary, get_exchange_rate, get_time_by_timezone, get_latest_news

#OPENAI_API_KEY = "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"
#client = OpenAI(api_key=OPENAI_API_KEY)

ALLOWED_APIS = {"get_current_weather", "get_current_temperature", "get_forecast", "get_wikipedia_summary", "get_exchange_rate", "get_time_by_timezone", "get_latest_news"}

# ====== API 說明（會放進 prompt）======
api_specs = {
    "get_current_weather": {
        "description": "Get **today's current weather description** (e.g., sunny, cloudy, rainy).",
        "params": ["location"]
    },
    "get_current_temperature": {
        "description": "Get **today's current temperature in Celsius**.",
        "params": ["location"]
    },
    "get_forecast": {
        "description": "Get **weather forecast for upcoming days**.",
        "params": ["location", "date(optional)", "days(optional, max 5)"]
    },
    "get_wikipedia_summary": {
        "description": "Get a short Wikipedia summary for the given query.",
        "params": ["query", "sentences(optional)"]
    },
    "get_exchange_rate": {
        "description": "Get the current exchange rate between two currencies (e.g., USD to JPY).",
        "params": ["base_currency", "target_currency"]
    },
    "get_time_by_timezone": {
        "description": "Get the current time for a given timezone (e.g., Asia/Taipei, Europe/London).",
        "params": ["timezone"]
    },
    "get_latest_news": {
        "description": "Get the latest 3 news headlines for a topic (e.g., AI, sports).",
        "params": ["query", "language(optional, default=en)"]
    }
}

api_description_text = "\n".join(
    [f"- {n}: {s['description']}, params: {', '.join(s['params'])}" for n, s in api_specs.items()]
)

# ====== 呼叫 real_api ======
def call_api(api_name, args):
    if "date" in args and (not isinstance(args["date"], str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", args["date"])):
        args.pop("date", None)
    try:
        if api_name == "get_current_weather":
            return get_current_weather(**args)
        elif api_name == "get_current_temperature":
            return get_current_temperature(**args)
        elif api_name == "get_forecast":
            return get_forecast(**args)
        elif api_name == "get_wikipedia_summary":
            return get_wikipedia_summary(**args)
        elif api_name == "get_exchange_rate":
            return get_exchange_rate(**args)
        elif api_name == "get_time_by_timezone":
            return get_time_by_timezone(**args)
        elif api_name == "get_latest_news":
            return get_latest_news(**args)
        else:
            return f"Error: Unknown API '{api_name}'"
    except Exception as e:
        return f"Error: {e}"

# ====== 呼叫 Ollama ======
def call_ollama(model: str, prompt: str, temperature: float = 0.7):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "options": {"temperature": temperature}
    }
    resp = requests.post(url, json=payload, stream=True)
    output = ""
    for line in resp.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            if "response" in data:
                output += data["response"]
    return output.strip()

# ====== 只抓第一個 { ... } ======
def safe_json_loads(s: str):
    match = re.search(r"\{[\s\S]*\}", s)
    if match:
        return json.loads(match.group(0))
    raise ValueError("No valid JSON found")

# ====== 單次嘗試 ======
def attempt_call(user_query, error_summary=None):
    """嘗試呼叫一次 API，並由 LLM 判斷 outcome。"""

    today_str = datetime.now().strftime("%Y-%m-%d (%A)")
    extra_hint = f"\nNote: Last error was '{error_summary}'. Try to avoid the same mistake." if error_summary else ""

    action_prompt = f"""
User query: "{user_query}"{extra_hint}

You must choose exactly ONE API from the list below and return its call in JSON.

Available APIs:
{api_description_text}

Rules:
- Today is {today_str}.
- api_name must match exactly one of the names above.
- args must strictly follow the listed parameters (no extra fields).
- If the user asks about a landmark, replace it with the nearest city (e.g., "Machu Picchu" → "Cusco, Peru").
- If a date is mentioned without a year, always use {datetime.now().year}.
- Output exactly ONE JSON object, with no extra text or explanation.

Format:
{{
  "api_name": "...",
  "args": {{ ... }}
}}
""".strip()

    action_resp = call_ollama("llama3", action_prompt, temperature=0.4)
    print("DEBUG action_resp:", action_resp)

    try:
        action_json = safe_json_loads(action_resp)
        api_name = action_json["api_name"]
        args = action_json.get("args", {})
        if api_name not in ALLOWED_APIS:
            raise ValueError(f"Disallowed API: {api_name}")
        observation = call_api(api_name, args)
    except Exception as e:
        api_name, args = "invalid", {}
        observation = f"Error: {e}"

    # === 由 LLM 產生 outcome ===
    reflection_prompt = f"""
You asked: "{user_query}"
API returned: "{observation}"

Decide the outcome:
- If the call was appropriate and helpful, reply exactly: success
- If not, reply exactly: error, followed by a short one-sentence reason summary
""".strip()

    refl = call_ollama("llama3", reflection_prompt, temperature=0).strip()
    print("DEBUG reflection:", refl)

    if refl.lower().startswith("success"):
        is_success = True
        outcome = "success"
    elif refl.lower().startswith("error"):
        is_success = False
        outcome = refl  # LLM 會輸出 "error, ..."
    else:
        is_success = False
        outcome = "error, LLM gave invalid reflection"

    return api_name, args, observation, is_success, outcome

# ====== 單次 trial，包含最多三輪嘗試 ======
def run_trial(short_term_memory, long_term_memory, episode_id, trial_id):
    # 生成 user query
    memory_snippets = ""
    for m in short_term_memory[-3:]:
        memory_snippets += f"- Q: {m['query']}\n  → Called: {m['api']}({m['args']})\n  → Success: {m['success']}\n"

    long_memory_snippets = ""
    for m in long_term_memory[-5:]:
        long_memory_snippets += f"- Q: {m['query']}\n  → API: {m['api']} → Success: {m['success']}\n"

    today_str = datetime.now().strftime("%Y-%m-%d (%A)")

    prompt = f"""
You are a creative assistant with access to the following APIs:
{api_description_text}

Today is {today_str}.
Only use ONE of these APIs: {', '.join(sorted(ALLOWED_APIS))}.

Previous episodes (summary):
{long_memory_snippets if long_memory_snippets else '(no long-term memory yet)'}

Recent trials in this episode:
{memory_snippets if memory_snippets else '(no recent trials yet)'}

Task:
Generate ONE natural and diverse user-style question that can be answered by exactly ONE of these APIs.
Requirements:
- Must be different in style, location, date, or subject from recent queries.
- Keep it conversational and realistic.
- Dates may be natural language (e.g., tomorrow, next weekend, 2025/09/25).
- Avoid repeating the same city or person often.
Output only the question text.
""".strip()

    user_query = call_ollama("llama3", prompt, temperature=0.9)

    error_summary = None
    final_result = None

    for round_id in range(1, 4):
        api_name, args, observation, is_success, outcome = attempt_call(user_query, error_summary)

        print(f"Round {round_id} → {api_name} {args} → {observation} → {outcome}")

        final_result = {
            "run_id": RUN_ID,
            "query": user_query,
            "api": api_name,
            "args": args,
            "observation": observation,
            "outcome": outcome,
            "success": is_success,
        }

        if is_success:
            break
        else:
            # 更新 error_summary 給下一輪參考
            error_summary = outcome.replace("error,", "").strip()

    short_term_memory.append(final_result)
    long_term_memory.append(final_result)

# ====== 儲存 ======
def _load_existing_trials(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_trials(new_trials, path="results/ste_trials.json"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = _load_existing_trials(path)
    merged = existing + new_trials
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    snapshot = os.path.join(os.path.dirname(path), f"ste_trials_{RUN_ID}.json")
    with open(snapshot, "w", encoding="utf-8") as f:
        json.dump(new_trials, f, indent=2, ensure_ascii=False)
    print(f"✅ Appended {len(new_trials)} trials. Total now: {len(merged)}")
    print(f"📄 Master: {os.path.abspath(path)}")
    print(f"🗂  Snapshot for this run: {os.path.abspath(snapshot)}")

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