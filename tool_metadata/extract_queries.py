import json
import os
import argparse

COMPLEX_APIS = [
    "calculate_mortgage_payment",
    "get_hotels_by_location",
    "get_restaurants_by_location",
    "get_divisions_near_location",
    "get_planet_data",
    "get_flights_in_bounding_box",
    "calculate_route",
    "list_of_deals",
    "search_businesses",
    "get_trades_futures"
]

SIMPLE_APIS = [
    "verify_email",
    "get_animal_facts",
    "search_public_restrooms",
    "get_dog_breeds_metadata",
    "get_media_news",
    "search_manga",
    "search_exercises_by_name",
    "get_financial_data",
    "convert_currency",
    "get_recipe",
    "search_streaming_shows",
    "search_cocktails",
    "get_filtered_game_giveaways",
    "get_lol_champion_stats",
    "get_salary_estimation",
    "get_airport_delay_statistics",
    "get_timezone_info",
    "get_celestial_body_position",
    "search_arxiv_papers",
    "get_handball_scheduled_matches",
    "get_airlines",
    "get_motorcycle_data",
    "get_air_quality_data",
    "get_weather_forecast",
    "search_amazon_products"
]

def process_apis(api_list, output_file, tool_test):
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            grouped_data = json.load(f)
    else:
        grouped_data = {}

    # Get the current maximum batch ID to continue numbering
    max_batch_id = -1
    for api, queries in grouped_data.items():
        for q in queries:
            qid = q.get("query_id", "")
            if qid.startswith("batch_"):
                try:
                    num = int(qid.split("_")[1])
                    if num > max_batch_id:
                        max_batch_id = num
                except ValueError:
                    pass

    next_batch_id = max_batch_id + 1
    added_count = 0

    for api_name in api_list:
        if api_name not in tool_test:
            print(f"Warning: API '{api_name}' not found in tool_test.json.")
            continue
            
        if api_name not in grouped_data:
            grouped_data[api_name] = []
            
        print(f"Extracting {len(tool_test[api_name])} queries for '{api_name}'...")
        for q in tool_test[api_name]:
            new_query = {
                "query": q["query"],
                "action_input": q["action_input"],
                "query_id": f"batch_{next_batch_id}",
                "target_intent_id": q.get("target_intent_id", 0)
            }
            grouped_data[api_name].append(new_query)
            next_batch_id += 1
            added_count += 1

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(grouped_data, f, indent=2, ensure_ascii=False)
        
    print(f"\nSuccess! Appended {added_count} queries to {output_file}.")

def main():
    parser = argparse.ArgumentParser(description="Extract APIs from tool_test.json and separate into complex and simple.")
    parser.add_argument("--type", choices=["complex", "simple", "both"], default="both", help="Which type of APIs to extract (default: both)")
    args = parser.parse_args()

    tool_test_path = "tool_metadata/tool_test.json"
    
    if not os.path.exists(tool_test_path):
        print(f"Error: {tool_test_path} not found.")
        return

    with open(tool_test_path, 'r', encoding='utf-8') as f:
        tool_test = json.load(f)

    if args.type in ["complex", "both"]:
        print("\n--- Processing Complex APIs ---")
        process_apis(COMPLEX_APIS, "tool_metadata/test_queries_complex.json", tool_test)
        
    if args.type in ["simple", "both"]:
        print("\n--- Processing Simple APIs ---")
        process_apis(SIMPLE_APIS, "tool_metadata/test_queries_simple.json", tool_test)

    print("\nIMPORTANT: The 'target_intent_id' for all new queries has been defaulted to 0.")
    print("If these APIs have multiple intents, please manually update the target_intent_id in the output files!")

if __name__ == "__main__":
    main()
