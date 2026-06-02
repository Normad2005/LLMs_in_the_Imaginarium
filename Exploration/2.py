INTENT_PROMPT = """\
You are analyzing an API to identify its distinct usage intents.

API name: __API_NAME__

API description:
__API_DESCRIPTION__

Task:
Identify the fundamentally different ways a user might call this API.
We are building tools for small language models (7-8B). Split an API into multiple intents ONLY when a small model would genuinely struggle to read the full description and know which parameters to use, because mixing different parameter groups in one document would cause confusion.

Rules for Splitting:
- Do NOT split if the API is simple enough that a small model can read the full description and immediately know what to fill in.
- Do NOT split if the only difference is which optional filter parameters are provided (fold them into one intent).
- Do NOT split if parameters are just different ways to narrow down the same type of query (e.g., search by make, by model, or by year — these are all just "look up motorcycle data with different filters").
- A GOOD split represents genuinely different user mental models where different parameter groups are relevant (e.g., `calculate_mortgage_payment` split into "I know my loan amount", "I know my home value and downpayment", "I want the full ownership cost").
- A BAD split divides an API by filter combinations (e.g., `get_motorcycle_data` split into 5 intents by filter).
- Rule of thumb: Ask, "If I only show a small model the description for this one intent, would it be unambiguous about which parameters to provide?" If yes for each intent and no for the combined description, split. Otherwise, keep it as exactly 1 intent.
- Maximum __MAX_INTENTS__ intents.

Output valid JSON only — no explanation, no markdown fences.
Format:
[
  {
    "intent_id": 0,
    "name": "<short English name>",
    "description": "<one sentence describing when this intent applies>",
    "key_parameters": ["<param1>", "<param2>"]
  }
]
"""