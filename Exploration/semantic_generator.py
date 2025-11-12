# === semantic_generator_v3b.py ===
import os
import re
import json
from collections import Counter
from typing import Dict, Any
from my_llm import call_ollama

# ---------- config ----------
DATA_PATH = "results/ste/data_20251028-002733.json"
TOOL_DESC_PATH = "tool_metadata/tool_description.json"
OUT_PATH = "results/semantic_memory.json"
MODEL_CKPT = "llama3.1:8b-instruct-fp16"

MAX_CHAINS_PER_SESSION = 6
MAX_EXAMPLES_PER_API = 6
MAX_PROMPT_EXAMPLES = 4
TRUNCATE_OBS_LEN = 800


# ---------- helpers ----------
def safe_json_loads(s: str):
    if not isinstance(s, str):
        return s
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
    parsed = safe_json_loads(action_input or "")
    if isinstance(parsed, dict):
        return {k: parsed[k] for k in sorted(parsed.keys())}
    return parsed


def extract_error_msg(obs: str):
    if not isinstance(obs, str):
        return ""
    if "error" in obs.lower():
        m = re.search(r"\{[\s\S]*?\}", obs)
        if m:
            return m.group(0)
        else:
            return obs.strip()[:200]
    return ""


def shorten(s: str, L=200):
    if not isinstance(s, str):
        return s
    return s if len(s) <= L else s[:L] + "..."


def parse_rule(resp: str):
    """Extract 'Rule: ...' line from LLM response."""
    if not resp:
        return None
    m = re.search(r"Rule\s*:\s*(.+)", resp)
    if m:
        return m.group(1).strip()
    return None


# ---------- core processing ----------
def collect_failed_examples(data: Dict[str, Any]):
    results = {}
    for api_name, sessions in data.items():
        failed = [s for s in sessions if s.get("reflection") == "No"]
        if not failed:
            continue

        examples = []
        error_counter = Counter()
        total_chains = 0
        missing_action_input_count = 0

        for s in failed:
            q = s.get("query", "")
            chains = s.get("chains", [])[:MAX_CHAINS_PER_SESSION]
            for c in chains:
                parsed = c.get("parsed", {})
                action = parsed.get("action", "")
                action_input_raw = parsed.get("action_input", "")
                action_input = normalize_action_input(action_input_raw)
                obs = c.get("observation", "")
                err = extract_error_msg(obs)
                if err:
                    error_counter[err] += 1
                if not action_input or action_input == {} or action_input == "":
                    missing_action_input_count += 1
                total_chains += 1
                examples.append({
                    "query": shorten(q, 240),
                    "action_input": action_input,
                    "error": shorten(err, 200)
                })

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

        # format top errors for readability
        top_err_list = []
        for e, c in error_counter.most_common(6):
            short = e.replace("\n", " ")[:200]
            top_err_list.append(f"[{c}x] {short}")

        results[api_name] = {
            "stats": {
                "total_failed_sessions": len(failed),
                "missing_action_input_count": missing_action_input_count,
                "top_errors": top_err_list
            },
            "examples": uniq_examples
        }
    return results


# ---------- prompt builder ----------
PROMPT_TEMPLATE = """
You are an assistant that writes a single actionable rule for an API, based on recurring failure traces.

API name: {api_name}
API description:
{api_description}

Summary statistics:
- total_failed_sessions: {total_failed_sessions}
- missing_action_input_count: {missing_action_input_count}
- top_errors (most common): {top_errors}

Representative failed attempts:
{examples_block}

Task:
Please carefully analyze what went wrong in these examples and explain:
- Why these failures occurred (the likely reasoning or parameter mistake)
- How to fix them or what rule to follow next time
Then finally summarize ONE clear actionable sentence starting with:
Rule: <your concise rule here>
"""


def build_prompt(api_name: str, api_desc: dict, info: dict, max_prompt_examples=4):
    s = info["stats"]
    examples = info["examples"][:max_prompt_examples]
    example_lines = [json.dumps(ex, ensure_ascii=False) for ex in examples]
    examples_text = "\n".join(example_lines) if example_lines else "None"

    prompt = PROMPT_TEMPLATE.format(
        api_name=api_name,
        api_description=json.dumps(api_desc, ensure_ascii=False, indent=2),
        total_failed_sessions=s["total_failed_sessions"],
        missing_action_input_count=s["missing_action_input_count"],
        top_errors="\n  ".join(s["top_errors"]) if s["top_errors"] else "None",
        examples_block=examples_text,
        max_prompt_examples=max_prompt_examples
    )
    return prompt


# ---------- main ----------
def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(TOOL_DESC_PATH, "r", encoding="utf-8") as f:
        tool_desc = json.load(f)

    failed_summary = collect_failed_examples(data)
    semantic_memory = {}

    for api_name, info in failed_summary.items():
        desc = tool_desc.get(api_name, {"description": "No description available."})
        prompt = build_prompt(api_name, desc, info, max_prompt_examples=MAX_PROMPT_EXAMPLES)

        try:
            resp = call_ollama(MODEL_CKPT, prompt, temperature=0)
            rule = parse_rule(resp)
            if not rule:
                rule = "(no rule extracted)"
                print(f"[WARN] No rule parsed for {api_name}")

            semantic_memory[api_name] = {
                "rule": rule,
                "_meta": {
                    "failed_sessions": info["stats"]["total_failed_sessions"],
                    "missing_action_input": info["stats"]["missing_action_input_count"]
                }
            }
            print(f"🧠 {api_name}: {rule}")

        except Exception as e:
            print(f"[ERROR] call_ollama failed for {api_name}: {e}")
            semantic_memory[api_name] = {"error": str(e)}

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(semantic_memory, f, indent=2, ensure_ascii=False)
    print(f"Saved semantic memory to {OUT_PATH}")


if __name__ == "__main__":
    main()
