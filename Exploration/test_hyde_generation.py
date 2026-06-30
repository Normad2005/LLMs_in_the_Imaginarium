import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Exploration.my_llm import chat_my

MODEL_CKPT = "llama3.1:8b-instruct-fp16"

failed_queries = [
    "Just finalizing my budget. Loan is $450,000, 30 years, 3.8% rate. Property taxes are $4000 a year. What's the payment?",
    "We want to buy a condo priced at $300,000. We can put down 20%, which is $60,000. The mortgage rate is 6.0% for 20 years. What's the payment?",
    "I'm purchasing a property worth $550k. My downpayment is $50k. The 15-year rate is currently 3.9%. What's the monthly burden?",
    "For our international widget, query the divisions near 51.50, -0.12 within a 100 km radius. Use HATEOAS links, limit to 5 per page, and display the names in German.",
    "I need 3 rooms for 6 adults in Berlin. Map boundaries: lat 52.50 to 52.53, lon 13.38 to 13.41. Check-in 2026-09-10, check-out 2026-09-17.",
    "I am in Paris right now. The area I'm searching is between latitudes 48.85 and 48.86, and longitudes 2.34 and 2.36. Limit the search to 20 restaurants.",
    "I'm planning a dinner in San Francisco. Bounding box: lat 37.77 to 37.79, lon -122.42 to -122.40. Show me the second page of 5 restaurants, display them in Japanese (ja_JP), and price them in JPY."
]

def generate_hyde_description(query):
    prompt = f"""You are a system analyzing a user's query.
User query: "{query}"

Please expand this query by describing the user's underlying intent, their goal, and the parameters they might need to provide, written in a first-person perspective.
Do not answer the query. Just describe the intent.

CRITICAL: You MUST explicitly list ANY constraints, conditions, or specific data entities mentioned in the query. Do NOT generalize or summarize them into broader concepts. Preserve the exact granularity of the user's specific requirements (e.g., quantities, formats, specific calculation elements).
CRITICAL RULE: You MUST write the expanded description entirely in ENGLISH, regardless of what language the user asks for in the results or uses in the query. The output must be pure English for semantic matching purposes.
Output ONLY the expanded description, no other text or introductory phrases."""

    messages = [{"role": "system", "content": "You are a helpful assistant that only outputs the requested description."}]
    messages, _ = chat_my(messages, prompt, visualize=False, model=MODEL_CKPT, return_tokens=True)
    return messages[-1]["content"].strip()

print("Testing NEW HyDE Prompt Generation on the 7 Missed Queries:\n")
for i, q in enumerate(failed_queries):
    print(f"--- Query {i+1} ---")
    print(f"Original: {q}")
    hyde = generate_hyde_description(q)
    print(f"New HyDE: {hyde}\n")
