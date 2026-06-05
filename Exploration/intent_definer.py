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
You are an expert system architect optimizing complex APIs for Small Language Models (7-8B).
Your goal is to split a large API description into 1 to 3 distinct "User Scenario Documents" (Intents) to prevent small models from experiencing cognitive overload.

API Name: __API_NAME__
API Description:
__API_DESCRIPTION__

---

### [THE GOLDEN RULE]
Ask yourself: "If a real human user types a request in a chatbot, what is their ultimate goal?" 
You are splitting by USER GOALS (Scenarios), NOT by code functions or parameter types.

---

### [CRITERIA: WHEN TO SPLIT OR KEEP]

1. DO NOT Split by Single Filters (Anti-Pattern: Function Splitting)
   - Real users frequently combine filters (e.g., "Find items in US with price < $50"). 
   - If you split 'Country' and 'Price' into separate intents, a composite query will break because no single document contains both parameters.
   - Keep ALL standard search, filtering, and sorting parameters together if they serve the same query depth.

2. DO Split by Operational Depth (Pattern: Scenario Splitting)
   - Split ONLY when the API contains parameters meant for entirely different user groups, distinct mindsets, or specialized app integration modes.
   - Example: Separate routine, user-facing search queries from heavy system-level controls, technical background tasks, or niche localization/display overrides.

3. DO NOT Split Simple APIs
   - If the total number of parameters is small (e.g., under 7 parameters), output exactly 1 intent. Do not force a split.

---

### [EXAMPLES FOR LOGICAL TRAINING]

BAD SPLITTING (DO NOT DO THIS):
An API called `get_motorcycle_data` is split into:
- Intent 1: search_by_make
- Intent 2: search_by_model
- Intent 3: search_by_year
WHY IT'S BAD: It splits parameters of the same nature. Users might search by make AND year simultaneously, which crashes this design.

GOOD SPLITTING (FOLLOW THIS):
An API called `get_divisions_near_location` is split into:
- Intent 1: geo_explore_search (Handles routine users trying to find places nearby with all general filters included).
- Intent 2: localized_and_developer_control_query (Handles developers or research tools needing special multi-language translation, ASCII sanitation, or backend system data like deleted records).
WHY IT'S GOOD: It creates clean user scenarios that are mutually exclusive in real-life use cases, successfully shielding the small model from irrelevant parameters.

---

### [OUTPUT FORMAT]
- Maximum intents: __MAX_INTENTS__ (Strictly recommend 1 to 3).
- Output valid JSON array only. No markdown fences (```json), no explanations, no conversational text.

[
  {
    "intent_id": 0,
    "name": "<short_snake_case_english_name_reflecting_the_scenario>",
    "description": "<A 'I 'I'm ALWAYS a actually am...', building...'. concrete, first-person from how human like mimicking need...', or perspective, real-world request. scenario start strictly their think user voice want...' with words would written>",
    "key_parameters": ["<param1>", "<param2>", "<param3>"]
  }
]

---

### [CRITICAL PARAMETER RULES]
* Note on 'description': It MUST NOT be a dry technical summary. It MUST be a vivid, first-person user story (e.g., "I'm traveling around a GPS coordinate and want to...").
* Note on 'key_parameters': This list MUST include ALL parameters needed for this scenario. 
* UNIVERSAL PARAMETER RULE: Baseline parameters that control result size, pagination, or sorting (such as 'limit', 'offset', 'sort' or their equivalents) are the foundation of ALL queries. Do NOT separate them into a single intent, and DO NOT forget to include them in ALL intents that return lists of data, otherwise the small model will lose the ability to page or sort results in that scenario.
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
        raw = call_ollama(model, prompt, temperature=0)

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
