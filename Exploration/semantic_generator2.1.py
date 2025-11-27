# === semantic_generator_v4_thought.py ===
"""
Semantic Generator 2.1
版本說明：
- 基於 v4（Semantic Generator 2.0）
- 額外將每個 chain 的 thought 加入到 examples 中
- Prompt 會一起顯示 thought，讓模型能從思考過程推導錯誤規則
"""

import os
import re
import json
from collections import Counter
from typing import Dict, Any
from my_llm import call_ollama

# ---------- config ----------
DATA_PATH = "results/ste/data_20251112-091248.json"
TOOL_DESC_PATH = "tool_metadata/tool_description.json"
OUT_PATH = "results/semantic_memory_v2_thought.json"
MODEL_CKPT = "llama3.1:8b-instruct-fp16"

MAX_CHAINS_PER_SESSION = 6
MAX_EXAMPLES_PER_API = 6
MAX_PROMPT_EXAMPLES = 4


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


# ---------- core logic ----------
def collect_problematic_examples(data: Dict[str, Any]):
    results = {}
    for api_name, sessions in data.items():
        bad_sessions = []
        for s in sessions:
            refl = str(s.get("reflection", "")).lower()
            if refl == "no":
                bad_sessions.append(s)
                continue
            if refl == "yes":
                chains = s.get("chains", [])
                for c in chains:
                    if c.get("parsed", {}).get("parse_successful") is False:
                        bad_sessions.append(s)
                        break

        if not bad_sessions:
            continue

        examples = []
        error_counter = Counter()
        missing_action_input_count = 0

        for s in bad_sessions:
            q = s.get("query", "")
            chains = s.get("chains", [])[:MAX_CHAINS_PER_SESSION]
            for c in chains:
                parsed = c.get("parsed", {})
                action = parsed.get("action", "")
                action_input_raw = parsed.get("action_input", "")
                action_input = normalize_action_input(action_input_raw)
                thought = parsed.get("thought", "")
                obs = c.get("observation", "")
                err = extract_error_msg(obs)

                if err:
                    error_counter[err] += 1
                if not action_input or action_input == {} or action_input == "":
                    missing_action_input_count += 1

                examples.append({
                    "query": shorten(q, 240),
                    "thought": shorten(thought, 240),
                    "action": action,
                    "action_input": action_input,
                    "error": shorten(err, 200)
                })

        # unique examples
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

        top_err_list = [f"[{c}x] {e.replace(chr(10), ' ')[:200]}" for e, c in error_counter.most_common(6)]

        results[api_name] = {
            "stats": {
                "total_problem_sessions": len(bad_sessions),
                "missing_action_input_count": missing_action_input_count,
                "top_errors": top_err_list
            },
            "examples": uniq_examples
        }
    return results


# ---------- prompt ----------
PROMPT_TEMPLATE = """
You are an assistant that writes a single actionable rule for an API, based on recurring failure traces.

API name: {api_name}
API description:
{api_description}

Summary statistics:
- total_problem_sessions: {total_problem_sessions}
- missing_action_input_count: {missing_action_input_count}
- top_errors (most common): {top_errors}

Representative problematic attempts (including the model's thought process):
{examples_block}

Task:
Please carefully analyze what went wrong in these examples, considering both the input/output and the thought process.
Explain:
- Why these failures occurred (reasoning or parameter mistakes)
- How to fix them or what rule to follow next time
Then summarize ONE clear actionable sentence starting with:
Rule: <your concise rule here>
"""


def build_prompt(api_name: str, api_desc: dict, info: dict, max_prompt_examples=4):
    s = info["stats"]
    examples = info["examples"][:max_prompt_examples]
    examples_text = "\n".join([json.dumps(ex, ensure_ascii=False) for ex in examples]) if examples else "None"

    return PROMPT_TEMPLATE.format(
        api_name=api_name,
        api_description=json.dumps(api_desc, ensure_ascii=False, indent=2),
        total_problem_sessions=s["total_problem_sessions"],
        missing_action_input_count=s["missing_action_input_count"],
        top_errors="\n  ".join(s["top_errors"]) if s["top_errors"] else "None",
        examples_block=examples_text,
    )


# ---------- main ----------
def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    with open(TOOL_DESC_PATH, "r", encoding="utf-8") as f:
        tool_desc = json.load(f)

    problematic_summary = collect_problematic_examples(data)
    semantic_memory = {}

    for api_name, info in problematic_summary.items():
        desc = tool_desc.get(api_name, {"description": "No description available."})
        prompt = build_prompt(api_name, desc, info, max_prompt_examples=MAX_PROMPT_EXAMPLES)

        try:
            resp = call_ollama(MODEL_CKPT, prompt, temperature=0)
            rule = parse_rule(resp) or "(no rule extracted)"
            if rule == "(no rule extracted)":
                print(f"[WARN] No rule parsed for {api_name}")

            semantic_memory[api_name] = {
                "rule": rule,
                "_meta": {
                    "problem_sessions": info["stats"]["total_problem_sessions"],
                    "missing_action_input": info["stats"]["missing_action_input_count"]
                }
            }
            print(f"{api_name}: {rule}")

        except Exception as e:
            print(f"[ERROR] call_ollama failed for {api_name}: {e}")
            semantic_memory[api_name] = {"error": str(e)}

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(semantic_memory, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved semantic memory (with thought) to {OUT_PATH}")


if __name__ == "__main__":
    main()
