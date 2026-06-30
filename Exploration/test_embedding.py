import os
import json
import numpy as np

INTENT_DEF_PATH = "results/intent_definitions.json"

hyde_texts = {
    # Query 1
    "calculate_mortgage_payment_intent1": "I'm trying to determine my monthly mortgage payment so I can finalize my budget. My goal is to understand how much I'll need to set aside each month to cover the loan. To do this, I'll need to provide specific information about the loan and property taxes.\n\nKey parameters I might need to provide include:\n\n* Loan amount: $450,000\n* Loan term: 30 years\n* Interest rate: 3.8%\n* Property taxes per year: $4,000\n\nConstraints and conditions that will affect my calculation include:\n\n* The interest rate is a fixed annual percentage rate (APR)\n* The property taxes are paid annually, but I want to know the monthly payment\n* The loan term is a specific number of years, not months or any other unit of time\n* I'm assuming the loan and property taxes will remain constant over the 30-year period\n\nI'll need to consider these factors when calculating my monthly mortgage payment.",
    
    # Query 2
    "calculate_mortgage_payment_intent2_1": "I want to calculate my monthly mortgage payment for a condo I'm planning to buy. My goal is to determine how much I'll need to pay each month so that I can budget accordingly. To do this, I need to provide some information about the condo and the loan.\n\nSpecifically, I need to know:\n\n* The purchase price of the condo: $300,000\n* The down payment amount: $60,000 (20% of the purchase price)\n* The mortgage interest rate: 6.0%\n* The length of the loan: 20 years\n\nConstraints and conditions:\n\n* I'm putting down a fixed percentage of the purchase price as a down payment.\n* The mortgage interest rate is a specific percentage value.\n* The loan term is a fixed number of years.\n\nData entities mentioned:\n\n* Purchase price ($300,000)\n* Down payment amount ($60,000)\n* Mortgage interest rate (6.0%)\n* Loan length (20 years)",
    
    # Query 3
    "calculate_mortgage_payment_intent2_2": "I'm trying to determine my monthly mortgage payments so I can understand how much I'll need to pay each month towards this property. My goal is to calculate the exact amount of money I'll have to set aside every month for the next 15 years, taking into account the current interest rate and the loan terms.\n\nTo do this, I think I'll need to provide some specific information about my mortgage:\n\n* The purchase price of the property: $550k\n* My down payment: $50k (which means my loan amount will be $500k)\n* The interest rate for a 15-year mortgage: 3.9%\n* The length of the mortgage: 15 years\n\nConstraints and conditions:\n\n* I'm looking to calculate monthly payments only.\n* I want to know the exact amount of money I'll need to pay each month, considering the interest rate and loan term.\n* The calculation should be based on a fixed interest rate for the entire 15-year period.",
    
    # Query 4
    "get_divisions_near_location_intent1": "I'm trying to retrieve a list of divisions near a specific geographic location (51.50, -0.12) within a particular radius (100 km). I want these results to be paginated with 5 items per page and displayed in German. \n\nTo achieve this, I'll need to provide the following parameters:\n\n* Latitude and longitude coordinates (51.50, -0.12)\n* Radius value (100 km)\n* Limit of records per page (5)\n* Language for result names (German)\n\nConstraints and conditions:\n\n* The results must be divisions\n* The results must be within a 100 km radius from the specified location\n* The results must be paginated with 5 items per page\n* The names of the divisions should be displayed in German\n\nSpecific data entities mentioned:\n\n* Latitude: 51.50\n* Longitude: -0.12\n* Radius: 100 km\n* Limit: 5 records per page\n* Language: German (for result names)",
    
    # Query 5
    "get_hotels_by_location_intent1": "I'm looking to book three separate rooms that can accommodate six adults in Berlin. My goal is to find suitable accommodations within a specific geographic area bounded by latitude 52.50 to 52.53 and longitude 13.38 to 13.41. I need to check-in on September 10, 2026, and check-out on September 17, 2026.\n\nConstraints:\n\n* Three separate rooms are required\n* The rooms must accommodate six adults\n* The location is in Berlin\n* Geographic boundaries:\n\t+ Latitude: 52.50 to 52.53\n\t+ Longitude: 13.38 to 13.41\n* Check-in date: September 10, 2026\n* Check-out date: September 17, 2026\n\nSpecific data entities:\n\n* Number of rooms: 3\n* Number of adults per room: Not explicitly stated (assuming six adults total, implying one or more adults per room)\n* Accommodation type: Not specified (e.g., hotel, apartment, hostel)\n* Location: Berlin, within the specified geographic boundaries",
    
    # Query 6
    "get_restaurants_by_location_intent0": "I'm trying to find restaurants near my current location in Paris that fall within a specific geographic area. My goal is to discover and list 20 suitable restaurant options within this range. \n\nConstraints:\n\n* The search area is bounded by latitudes 48.85 and 48.86\n* The search area is bounded by longitudes 2.34 and 2.36\n* I'm limiting the results to exactly 20 restaurants\n\nParameters I might need to provide or confirm:\n\n* My current location in Paris (already provided)\n* The latitude and longitude bounds for the search area (already specified as 48.85-48.86 and 2.34-2.36, respectively)",
    
    # Query 7
    "get_restaurants_by_location_intent1": "I'm planning a dinner in San Francisco and I need help finding suitable restaurants within a specific geographic area. My goal is to discover and list 5 restaurants that meet my criteria, specifically:\n\n* Located within a bounding box defined by latitude (37.77 to 37.79) and longitude (-122.42 to -122.40)\n* Displaying the results in Japanese language (ja_JP)\n* Pricing the results in Japanese Yen (JPY)\n\nTo achieve this goal, I might need to provide or specify:\n* The exact coordinates of the bounding box\n* A minimum or maximum price range for the restaurants\n* Any specific cuisine type or restaurant characteristics I'm interested in\n* A limit on the number of pages or results displayed\n\nConstraints and conditions mentioned in my query include:\n* Bounding box defined by latitude 37.77 to 37.79 and longitude -122.42 to -122.40\n* Language for displaying results: Japanese (ja_JP)\n* Currency for pricing results: Japanese Yen (JPY)\n* Specific page number requested: second page\n* Number of restaurants per page: 5"
}

ground_truths = {
    "calculate_mortgage_payment_intent1": ("calculate_mortgage_payment", 1),
    "calculate_mortgage_payment_intent2_1": ("calculate_mortgage_payment", 2),
    "calculate_mortgage_payment_intent2_2": ("calculate_mortgage_payment", 2),
    "get_divisions_near_location_intent1": ("get_divisions_near_location", 1),
    "get_hotels_by_location_intent1": ("get_hotels_by_location", 1),
    "get_restaurants_by_location_intent0": ("get_restaurants_by_location", 0),
    "get_restaurants_by_location_intent1": ("get_restaurants_by_location", 1),
}

def cosine_similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def main():
    print("Loading SentenceTransformer model...")
    try:
        from sentence_transformers import SentenceTransformer
        import torch
        embedder = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    except Exception as e:
        print(f"Failed to load: {e}")
        return

    with open(INTENT_DEF_PATH, 'r', encoding='utf-8') as f:
        intent_defs = json.load(f)

    all_intents = []
    for api_name, api_data in intent_defs.items():
        for intent in api_data.get("intents", []):
            desc = intent["description"]
            full_text = f"API: {api_name}. Intent: {intent['name']}. Description: {desc}"
            all_intents.append({
                "api_name": api_name,
                "intent_id": intent["intent_id"],
                "text": full_text
            })
            
    print("Embedding API Intents...")
    intent_texts = [i["text"] for i in all_intents]
    intent_embeddings = embedder.encode(intent_texts)
    
    for i, emb in enumerate(intent_embeddings):
        all_intents[i]["embedding"] = emb

    print("\n--- Evaluating the 7 previously failed queries ---")
    for key, text in hyde_texts.items():
        target_api, target_intent = ground_truths[key]
        query_emb = embedder.encode([text])[0]
        
        api_best_intents = {}
        for intent in all_intents:
            score = float(cosine_similarity(query_emb, intent["embedding"]))
            api = intent["api_name"]
            if api not in api_best_intents or score > api_best_intents[api]["score"]:
                api_best_intents[api] = {"api_name": api, "intent_id": intent["intent_id"], "score": score}
                
        sorted_best_apis = sorted(api_best_intents.values(), key=lambda x: x["score"], reverse=True)
        top1 = sorted_best_apis[0]
        
        print(f"\nQuery: {key}")
        print(f"  Ground Truth: {target_api} (Intent {target_intent})")
        print(f"  Top-1 Ret:    {top1['api_name']} (Intent {top1['intent_id']}) - Score: {top1['score']:.4f}")
        
        if top1['api_name'] == target_api and top1['intent_id'] == target_intent:
            print("  ==> [RESCUED] Success!")
        else:
            print("  ==> [MISS]")
            # print actual target score
            for r in sorted_best_apis:
                if r['api_name'] == target_api and r['intent_id'] == target_intent:
                    print(f"      (Target scored {r['score']:.4f})")
                    break

if __name__ == "__main__":
    main()
