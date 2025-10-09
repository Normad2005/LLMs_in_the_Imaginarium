# === ste_runner.py ===
import sys
import os
import json
import re
from datetime import datetime
import requests

RUN_ID = datetime.now().strftime("%Y%m%d-%H%M%S")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from real_api import get_current_weather, get_current_temperature, get_forecast, get_wikipedia_summary, get_exchange_rate, get_time_by_timezone, get_latest_news

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

# ====== call real_api ======
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

# ====== call Ollama ======
def call_ollama(model, prompt, temperature=0.7):
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "options": {"temperature": temperature}}
    resp = requests.post(url, json=payload, stream=True)
    output = ""
    for line in resp.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            if "response" in data:
                output += data["response"]
    return output.strip()

# ====== safe JSON parser ======
def safe_json_loads(s: str):
    match = re.search(r"\{[\s\S]*\}", s)
    if not match:
        raise ValueError("No valid JSON found")

    json_str = match.group(0)
    # remove comments
    json_str = re.sub(r"//.*?(?=\n|$)", "", json_str)
    json_str = re.sub(r"/\*[\s\S]*?\*/", "", json_str)
    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*\]", "]", json_str)
    json_str = json_str.strip()
    return json.loads(json_str)

# ====== ReAct with success-based reasoning ======
def attempt_call(user_query):
    today_str = datetime.now().strftime("%Y-%m-%d (%A)")
    MAX_TURNS = 4
    previous_steps = [{
    "thought": "(no previous thought)",
    "api_name": "(none yet)",
    "args": {},
    "observation": "(no observation yet)"
    }]

    prompt_header = f"""
Your task is to help answer the user's query using one of the following APIs.

{api_description_text}

Today is {today_str}.
You will reason step-by-step. At each step, you may choose one API to call.

Rules:
- If you want to make an API call, include:
  - "thought": your reasoning
  - "api_name": the API to call
  - "args": a JSON object with its arguments
  - "success": "false"
- If the the observation of your previous API call was appropriate for the question
  - "success": "true"
- You will receive the "observation" (API output) after each call.
- If the API output seems incomplete, that’s an API limitation, not an error in API choice.
- Output exactly ONE JSON object, with no extra text or explanation.

Format:
{{
  "thought": "reasoning here",
  "api_name": "API name",
  "args": {{
    "key": "value",
    "key": "value"
  }},
  "success": "false"
}}
last step:
{{
  "success": "true"
}}

User Query: {user_query}
""".strip()

    conversation = prompt_header + "\n\nBegin!\n"
    api_name, args, observation = None, {}, None
    final_answer, last_thought = None, None

    for turn in range(MAX_TURNS):
        memory_block = ""
        if previous_steps:
            memory_block = "\nPrevious steps:\n"
            for i, step in enumerate(previous_steps, 1):
                memory_block += f"Step {i}:\nThought: {step['thought']}\nObservation: {step['observation']}\n\n"

        react_prompt = conversation + memory_block + f"\n(Step {turn+1})\n"
        react_output = call_ollama("llama3", react_prompt, temperature=0.4)
        print(f"\n=== ReAct Turn {turn+1} ===\n{react_output}\n")

        # --- 解析 JSON ---
        try:
            step_obj = safe_json_loads(react_output)
            thought = step_obj.get("thought")
            success_flag = str(step_obj.get("success", "false")).lower() == "true"
            api_name = step_obj.get("api_name")
            args = step_obj.get("args", {})
        except Exception as e:
            observation = f"Error parsing JSON: {e}"
            print(f">>> Observation: {observation}")
            continue

        # --- 第一步不可 success=true ---
        if turn == 0 and success_flag:
            print("⚠️  Model marked success=true on Step 1, forcing to false.")
            success_flag = False

        # --- 若 success=true 則不呼叫 API ---
        if not success_flag:
            if api_name in ALLOWED_APIS:
                observation = call_api(api_name, args)
            else:
                observation = f"Error: Unknown or missing API '{api_name}'"
        else:
            observation = previous_steps[-1]["observation"] if previous_steps else "No prior observation"

        print(f">>> Observation: {observation}\n")

        # --- 記錄本輪 ---
        previous_steps.append({
            "thought": thought,
            "observation": observation,
            "api_name": api_name,
            "args": args,
            "success": success_flag
        })
        last_thought = thought

        # --- 若成功就結束 ---
        if success_flag:
            break

        conversation += f"\nObservation: {observation}\n"

    # === 生成最終回答 ===
    answer_prompt = f"""
User Query: {user_query}
Last Observation: {observation}

Write a concise, natural final answer for the user based on the observation.
If the observation is incomplete, explain that this may be due to API limitations.
Final Answer:
""".strip()

    final_answer = call_ollama("llama3", answer_prompt, temperature=0.4).strip()
    desc = api_specs.get(api_name, {}).get("description", "N/A")

    return api_name, args, observation, final_answer, last_thought, desc, success_flag

# ====== Trial ======
def run_trial(short_term_memory, long_term_memory, episode_id, trial_id):
    today_str = datetime.now().strftime("%Y-%m-%d (%A)")

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

    user_query = call_ollama("llama3", prompt, temperature=0.4)
    api_name, args, observation, final_answer, thought, desc, success_flag = attempt_call(user_query)

    final_result = {
        "run_id": RUN_ID,
        "query": user_query,
        "api": api_name,
        "api_description": desc,
        "args": args,
        "observation": observation,
        "final_ans": final_answer,
        "thought": thought,
        "success": success_flag
    }

    print(json.dumps(final_result, indent=2, ensure_ascii=False))
    short_term_memory.append(final_result)
    long_term_memory.append(final_result)

# ====== Save results ======
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

# ====== Main ======
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
