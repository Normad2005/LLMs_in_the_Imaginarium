# === intent_definer.py ===
import os
import re
import json
import argparse
from my_llm import call_ollama

# ---------- config ----------
TOOL_DESC_PATH = "tool_metadata/tool_description.json"
OUT_PATH       = "results/intent_definitions.json"
LLM_MODEL      = "gpt-oss:120b"
MAX_INTENTS    = 6   # hard upper bound — LLM is asked to respect this


# ---------- prompt ----------
# Uses __KEY__ placeholders to avoid .format() misinterpreting JSON braces.
INTENT_PROMPT = """\
You are analyzing an API to identify its distinct usage intents.

API name: __API_NAME__

API description:
__API_DESCRIPTION__

Task:
Identify the fundamentally different ways a user might call this API.
We are building tools for small language models (7-8B). Split an API into multiple intents ONLY when a small model would genuinely struggle to read the full description and know which parameters to use, because mixing different parameter groups in one document would cause confusion.

Default to 1 intent. Only split when you can clearly articulate why the combined document would confuse a small model.

Rules for splitting:
- Do NOT split if the API is simple enough that a small model can immediately know what to fill in.
- Do NOT split if the only difference is which optional filter parameters are provided.
- Do NOT split if parameters are just different ways to narrow down the same type of query.
- A GOOD split represents genuinely different user mental models where a small model reading only one intent's document would know exactly which parameters to provide, but would be confused by the combined document.
- A BAD split divides an API by filter combinations.

BAD split example: get_motorcycle_data split into 5 intents (by make only / model only / year only / make+model / make+model+year). All serve the same goal. A small model handles all filter combinations from one document.

GOOD split example: calculate_mortgage_payment split into 3 intents: "I know my loan amount", "I know my home value and downpayment", "I want the full ownership cost including HOA and insurance". Each intent involves a clearly different parameter group that would be confusing if mixed together.

Rule of thumb: Ask, "If I only show a small model the description for this one intent, would it be unambiguous about which parameters to provide?" If yes for each intent and no for the combined description, the split is justified. Otherwise, output exactly 1 intent.

Maximum __MAX_INTENTS__ intents.

Output valid JSON only — no explanation, no markdown fences.
Format:
[
  {
    "intent_id": 0,
    "name": "<short English name>",
    "description": "<one sentence from the user's perspective: what they are trying to accomplish>",
    "key_parameters": ["<params central to this intent that would be confusing if mixed with other intents>"]
  }
]
"""


def build_prompt(api_name: str, api_desc: dict) -> str:
    desc_str = json.dumps(api_desc, indent=2, ensure_ascii=False)
    return (
        INTENT_PROMPT
        .replace("__API_NAME__", api_name)
        .replace("__API_DESCRIPTION__", desc_str)
        .replace("__MAX_INTENTS__", str(MAX_INTENTS))
    )


# ---------- LLM call + parsing ----------
def llm_define_intents(api_name: str, api_desc: dict, model: str) -> list:
    """
    Ask the LLM to enumerate the distinct usage intents for one API.
    Returns a list of intent dicts; falls back to a single default intent
    on any parsing failure.
    """
    prompt = build_prompt(api_name, api_desc)

    try:
        raw, _prompt_tokens = call_ollama(model, prompt, temperature=0)

        # Extract the first JSON array from the response
        m = re.search(r"\[[\s\S]*\]", raw)
        if not m:
            raise ValueError("No JSON array found in LLM response")

        parsed = json.loads(m.group(0))

        if not isinstance(parsed, list) or len(parsed) == 0:
            raise ValueError("LLM returned an empty or non-list JSON")

        # Normalise and re-index so intent_ids are always 0-based integers
        intents = []
        for i, item in enumerate(parsed):
            intents.append({
                "intent_id":      i,
                "name":           str(item.get("name", f"Intent {i}")),
                "description":    str(item.get("description", "")),
                "key_parameters": list(item.get("key_parameters", [])),
            })
        return intents

    except Exception as exc:
        print(f"    [WARN] Intent definition failed for '{api_name}': {exc}")
        return [{
            "intent_id":      0,
            "name":           "Default Usage",
            "description":    f"General usage of the {api_name} API.",
            "key_parameters": [],
        }]


# ---------- main ----------
def main(
    tool_desc_path: str = TOOL_DESC_PATH,
    out_path:       str = OUT_PATH,
    model:          str = LLM_MODEL,
    overwrite:      bool = False,
):
    print(f"📂 Loading tool descriptions from: {tool_desc_path}")
    with open(tool_desc_path, "r", encoding="utf-8") as f:
        tool_desc: dict = json.load(f)

    # Load existing results so we can resume interrupted runs
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if not overwrite and os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            result: dict = json.load(f)
        print(f"🔄 Resuming — {len(result)} API(s) already processed.")
    else:
        result: dict = {}

    api_list = list(tool_desc.keys())
    total    = len(api_list)

    for idx, api_name in enumerate(api_list, start=1):
        if api_name in result:
            print(f"[{idx}/{total}] ⏭  Skipping '{api_name}' (already done)")
            continue

        print(f"\n[{idx}/{total}] ===== {api_name} =====")
        api_desc = tool_desc[api_name]

        intents = llm_define_intents(api_name, api_desc, model)

        print(f"    → {len(intents)} intent(s) defined:")
        for intent in intents:
            print(f"      [{intent['intent_id']}] {intent['name']}: {intent['description']}")

        result[api_name] = {"intents": intents}

        # Write after every API so progress is not lost on interruption
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Intent definitions saved to {out_path}")
    print(f"   Total APIs processed: {len(result)}")


# ---------- CLI ----------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Define usage intents for each API before STE exploration."
    )
    parser.add_argument(
        "--tool_desc", default=TOOL_DESC_PATH,
        help="Path to tool_description.json  (default: %(default)s)"
    )
    parser.add_argument(
        "--out", default=OUT_PATH,
        help="Output path for intent_definitions.json  (default: %(default)s)"
    )
    parser.add_argument(
        "--model", default=LLM_MODEL,
        help="LLM model checkpoint to use  (default: %(default)s)"
    )
    parser.add_argument(
        "--overwrite", action="store_true",
        help="Overwrite existing output instead of resuming"
    )
    args = parser.parse_args()

    main(
        tool_desc_path=args.tool_desc,
        out_path=args.out,
        model=args.model,
        overwrite=args.overwrite,
    )
