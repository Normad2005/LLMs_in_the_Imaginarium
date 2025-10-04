import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"


def generate_semantic_rule(cluster, model=OLLAMA_MODEL):
    """
    我要去改ste讓他outcome加入錯誤訊息
    cluster: list of dict
      - query
      - api
      - args
      - observation (str)
      - outcome
    """

    examples = """
Here are the examples of how to generalize trials into semantic rules:

Trials:
"query": "I'm curious, will it rain in Taichung next Monday?" 
"api": get_forecast 
"args": {"city": "Taichung", "date": "2025-10-04"} 
"observation": "It will rain in Taichung next Monday" 
"outcome": error, today is 2025-10-03(Friday), next Monday is not 2025-10-04

"query": "What's the weather like in Taipei this Sunday?",
"api": "get_forecast",
"args": {"city": "Taipei", "date": "2025-10-03"},
"observation": "Clear skies expected on 2025-10-03",
"outcome": "error, system mapped 'this Sunday' incorrectly (used current date instead of calculating weekday offset)"

Rule (desired): If the query mentions a day of the week (e.g., Monday, Friday), resolve it relative to today's date (2025-10-04) and use the correct calendar date when calling the forecast API.
"""

    # 把 cluster trials 轉成文字
    trials_text = []
    for t in cluster:
        trials_text.append(
            f'Q: "{t["query"]}" | API: {t["api"]} | args: {json.dumps(t["args"])} | outcome: {t["outcome"]}'
        )
    trials_text = "\n".join(trials_text)

    prompt = f"""
You are a semantic abstraction engine. Your job is to read a group of similar trials
and summarize the underlying rule that can guide future API selection.

{examples}

Now here is the new cluster of trials:
{trials_text}

Please output ONE clear, generalized rule in English.
"""

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    resp = requests.post(OLLAMA_URL, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data["response"].strip()


# --- Example usage ---
if __name__ == "__main__":
    cluster = [
        {
            "query": "What's the weather like in Paris for my trip to Disneyland this Saturday?",
            "api": "get_current_weather",
            "args": {"location": "Paris"},
            "observation": "The weather in Paris now is scattered clouds.",
            "outcome": "error, user asked about future but current weather API was used"
        },
        {
            "query": "Can you tell me if it will rain in Tokyo next Friday evening?",
            "api": "get_current_weather",
            "args": {"location": "Tokyo"},
            "observation": "The weather in Tokyo now is clear skies.",
            "outcome": "error, wrong API call (should use forecast for a future date)"
        },
        {
            "query": "I’m planning a picnic in New York tomorrow, how’s the weather?",
            "api": "get_current_weather",
            "args": {"location": "New York"},
            "observation": "Currently sunny in New York.",
            "outcome": "error, current weather cannot answer future query"
        }
    ]


    rule = generate_semantic_rule(cluster)
    print("Generated Rule:", rule)

