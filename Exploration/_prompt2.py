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
   - Split ONLY when the API contains parameters meant for entirely different user groups or modes.
   - Example: Separate routine, user-facing search queries from heavy system-level controls, technical background tasks, or niche localization/display overrides.

3. DO NOT Split Simple APIs
   - If the total number of parameters is small (e.g., under 5 parameters), output exactly 1 intent. Do not force a split.

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
- Intent 1: proximity_geographic_exploration (Contains: location, radius, and ALL query filters like country, timezone, population, name prefix, and sorting. This handles 95% of routine user searches without missing parameters).
- Intent 2: localized_and_system_override (Contains: location, radius, plus niche formatting/system parameters like languageCode, asciiMode, includeDeleted. This keeps these confusing engineering flags away from routine search tasks).
WHY IT'S GOOD: It creates 2 clean user scenarios that are mutually exclusive in real-life use cases, successfully shielding the small model from irrelevant parameters.

---

### [OUTPUT FORMAT]
- Maximum intents: __MAX_INTENTS__ (Strictly recommend 1 to 3).
- Output valid JSON array only. No markdown fences (```json), no explanations, no conversational text.

[
  {
    "intent_id": 0,
    "name": "<short_snake_case_english_name_reflecting_the_scenario>",
    "description": "<A concrete real-world user scenario written from a user's conversational perspective or a specific application workflow. E.g., 'A traveler searching for towns around their current GPS coordinates, optionally filtering by specific countries, time zones, or populations, and wanting sorted results.'>",
    "key_parameters": ["<param1>", "<param2>", "<param3>"]
  }
]

* Note on 'description': The description MUST NOT be a dry technical summary. It MUST describe a vivid, real-world user story, conversational persona, or specific end-user scenario so that an LLM or router can immediately map a human query to it.
* Note on 'key_parameters': This list MUST include ALL parameters needed for this scenario (both the global required parameters and the scenario-specific optional parameters), completely filtering out irrelevant parameters. Do NOT use generic names like "basic" or "advanced"; name them based on the real-world scenario.
"""