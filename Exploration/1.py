INTENT_PROMPT = """\
You are analyzing an API to identify its distinct usage intents.

API name: __API_NAME__

API description:
__API_DESCRIPTION__

Task:
Identify the fundamentally different ways a user might call this API.
"Fundamentally different" means the core PURPOSE or the primary parameter GROUP
changes between intents — not just whether optional/pagination parameters are filled.

Rules:
- If all calls to this API serve the same core purpose, output exactly 1 intent.
- Do NOT split intents based on different VALUES of the same parameter
  (e.g., different city names for a weather API is NOT a different intent).
- Do NOT create a separate intent just for default usage, pagination, or
  optional formatting parameters — fold these into the relevant intent's
  key_parameters list instead.
- Only split when the user's GOAL is different and requires a clearly distinct
  parameter group (e.g., searching by location vs. searching by ingredient).
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