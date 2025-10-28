# === semantic_generator_v2.py ===
import os
import json
import re
from collections import Counter, defaultdict
from typing import List, Dict, Any
from my_llm import call_ollama

# ---------- config ----------
DATA_PATH = "results/ste/data_20251028-002733.json"
TOOL_DESC_PATH = "tool_metadata/tool_description.json"
OUT_PATH = "results/semantic_memory_v2.json"
MODEL_CKPT = "llama3"

MAX_CHAINS_PER_SESSION = 6
MAX_EXAMPLES_PER_API = 6
MAX_PROMPT_EXAMPLES = 4
TRUNCATE_OBS_LEN = 800  # when including observations in prompt, truncate long strings

# ---------- helpers ----------
def safe_json_loads(s: str):
    """
    Attempt to extract and load JSON-like substring. Returns original string if fails.
    """
    if not isinstance(s, str):
        return s
    # find first { ... } block
    m = re.search(r"\{[\s\S]*\}", s)
    if not m:
        return s.strip()
    js = m.group(0)
    js = re.sub(r",\s*}", "}", js)
    js = re.sub(r",\s*\]", "]", js)
    try:
        return json.loads(js)
    except Exception:
        return js.strip()

def normalize_action_input(action_input: str):
    """Return a canonical dict or string for action_input"""
    parsed = safe_json_loads(action_input or "")
    if isinstance(parsed, dict):
        # sort keys for deterministic display
        return {k: parsed[k] for k in sorted(parsed.keys())}
    return parsed

def extract_error_msg(obs: str):
    if not isinstance(obs, str):
        return ""
    # common patterns
    if "error" in obs.lower():
        # try to extract JSON error
        m = re.search(r"\{[\s\S]*?\}", obs)
        if m:
            return m.group(0)
        else:
            # fallback: first 120 chars
            return obs.strip()[:200]
    return ""

def shorten(s: str, L=200):
    if not isinstance(s, str):
        return s
    return s if len(s) <= L else s[:L] + "..."

# ---------- core processing ----------
def collect_failed_examples(data: Dict[str, Any]):
    """
    For each api_name in data, collect sessions with reflection == "No",
    extract simplified chain entries, normalize action_input and extract error messages.
    Returns per-api dict with stats and examples.
    """
    results = {}
    for api_name, sessions in data.items():
        failed = [s for s in sessions if s.get("reflection") == "No"]
        if not failed:
            continue

        examples = []
        error_counter = Counter()
        missing_action_input_count = 0
        total_chains = 0

        for s in failed:
            q = s.get("query", "")
            chains = s.get("chains", [])[:MAX_CHAINS_PER_SESSION]
            for c in chains:
                parsed = c.get("parsed", {})
                thought = parsed.get("thought", "")
                action = parsed.get("action", "")
                action_input_raw = parsed.get("action_input", "")
                action_input = normalize_action_input(action_input_raw)
                obs = c.get("observation", "")
                err = extract_error_msg(obs)
                if err:
                    error_counter[err] += 1
                if (not action_input) or action_input == {} or action_input == "":
                    missing_action_input_count += 1
                total_chains += 1

                examples.append({
                    "query": shorten(q, 240),
                    "thought": shorten(thought, 200),
                    "action": action,
                    "action_input": action_input,
                    "observation": shorten(obs, TRUNCATE_OBS_LEN),
                    "error": shorten(err, 200)
                })

        # dedupe examples by action_input string
        seen = set()
        uniq_examples = []
        for ex in examples:
            key = json.dumps(ex["action_input"], ensure_ascii=False, sort_keys=True) if isinstance(ex["action_input"], dict) else str(ex["action_input"])
            if key in seen:
                continue
            seen.add(key)
            uniq_examples.append(ex)
            if len(uniq_examples) >= MAX_EXAMPLES_PER_API:
                break

        stats = {
            "total_failed_sessions": len(failed),
            "total_chains_examined": total_chains,
            "missing_action_input_count": missing_action_input_count,
            "top_errors": error_counter.most_common(6)
        }
        results[api_name] = {
            "stats": stats,
            "examples": uniq_examples
        }
    return results

# ---------- prompt builder ----------
PROMPT_TEMPLATE = """
You are an assistant that writes concise *actionable* usage rules for an API given failure traces.

API name: {api_name}
API description:
{api_description}

Summary statistics:
- total_failed_sessions: {total_failed_sessions}
- total_chains_examined: {total_chains_examined}
- missing_action_input_count: {missing_action_input_count}
- top_errors (most common): {top_errors}

Representative failed attempts (max {max_prompt_examples}):
{examples_block}

Task:
1) Based on the API description, statistics, and the failed attempts, produce a *single short rule sentence* that tells a developer/agent how to correctly use this API. Keep it actionable and specific (e.g., which parameters to provide, formatting/encoding, rate limits to respect, what NOT to include).
2) Also output a short structured JSON object (only JSON) with these keys:
   {{
     "rule": "<the single sentence>",
     "why": "<1-2 short sentences about the recurring failure cause>",
     "inputs_to_check": ["param1","param2",...],
     "common_errors": [{{"error": "<short msg>", "count": N}}, ...],
     "examples": [ <list of up to {max_prompt_examples} representative example objects (query/action_input/error)> ]
   }}

Important:
- Output strictly JSON only (no surrounding explanation).
- Keep all strings concise.
"""

def build_prompt(api_name: str, api_desc: dict, info: dict, max_prompt_examples=4):
    s = info["stats"]
    examples = info["examples"][:max_prompt_examples]
    examples_block = []
    for ex in examples:
        examples_block.append(json.dumps({
            "query": ex["query"],
            "action_input": ex["action_input"],
            "error": ex["error"]
        }, ensure_ascii=False))
    examples_text = "\n".join(examples_block) if examples_block else "None"
    prompt = PROMPT_TEMPLATE.format(
        api_name=api_name,
        api_description=json.dumps(api_desc, ensure_ascii=False, indent=2),
        total_failed_sessions=s["total_failed_sessions"],
        total_chains_examined=s["total_chains_examined"],
        missing_action_input_count=s["missing_action_input_count"],
        top_errors=", ".join([f"{e} ({c})" for e, c in s["top_errors"]]) if s["top_errors"] else "None",

        examples_block=examples_text,
        max_prompt_examples=max_prompt_examples
    )
    return prompt

# ---------- main ----------
def main():
    # load data
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(TOOL_DESC_PATH, "r", encoding="utf-8") as f:
        tool_desc = json.load(f)

    # collect failed examples & stats
    failed_summary = collect_failed_examples(data)

    semantic_memory = {}
    for api_name, info in failed_summary.items():
        desc = tool_desc.get(api_name, {"description": "No description available."})
        prompt = build_prompt(api_name, desc, info, max_prompt_examples=MAX_PROMPT_EXAMPLES)
        # call local Llama
        try:
            # deterministic
            resp = call_ollama(MODEL_CKPT, prompt, temperature=0)
            # model should return JSON only — try to parse
            # extract first JSON object in response
            m = re.search(r"\{[\s\S]*\}", resp)
            if not m:
                print(f"[WARN] No JSON response for {api_name}, saving raw text.")
                semantic_memory[api_name] = {"rule_raw": resp}
                continue
            js = json.loads(m.group(0))
            semantic_memory[api_name] = js
            # add some metadata
            semantic_memory[api_name]["_meta"] = {
                "generated_from_failed_sessions": info["stats"]["total_failed_sessions"],
                "examined_chains": info["stats"]["total_chains_examined"]
            }
            print(f"🧠 Generated for {api_name}: {semantic_memory[api_name].get('rule','(no rule)')}")
        except Exception as e:
            print(f"[ERROR] call_ollama failed for {api_name}: {e}")
            semantic_memory[api_name] = {"error": str(e)}

    # write out
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(semantic_memory, f, indent=2, ensure_ascii=False)
    print(f"Saved semantic memory to {OUT_PATH}")

if __name__ == "__main__":
    main()
