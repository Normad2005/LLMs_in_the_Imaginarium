import json
import os
import argparse

# List of APIs you want to extract (you can edit this directly!)
APIS_TO_TEST = [
    "calculate_mortgage_payment",
    "get_hotels_by_location",
    "get_restaurants_by_location",
    "get_divisions_near_location",
    "get_planet_data",
    "get_flights_in_bounding_box",
    "calculate_route",
]

def main():
    parser = argparse.ArgumentParser(description="Extract specific APIs from tool_test.json and append to test_queries_grouped.json")
    parser.add_argument("api_names", nargs="*", help="List of API names to extract (optional, will use APIS_TO_TEST if empty)")
    args = parser.parse_args()

    # Determine which APIs to extract: CLI args override the hardcoded list
    target_apis = args.api_names if args.api_names else APIS_TO_TEST
    
    if not target_apis:
        print("Error: No APIs specified. Please provide them via command line or edit APIS_TO_TEST in the script.")
        return

    tool_test_path = "tool_metadata/tool_test.json"
    grouped_path = "tool_metadata/test_queries_grouped.json"

    if not os.path.exists(tool_test_path):
        print(f"Error: {tool_test_path} not found.")
        return

    with open(tool_test_path, 'r', encoding='utf-8') as f:
        tool_test = json.load(f)

    if os.path.exists(grouped_path):
        with open(grouped_path, 'r', encoding='utf-8') as f:
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

    for api_name in target_apis:
        if api_name not in tool_test:
            print(f"Warning: API '{api_name}' not found in {tool_test_path}.")
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

    with open(grouped_path, 'w', encoding='utf-8') as f:
        json.dump(grouped_data, f, indent=2, ensure_ascii=False)
        
    print(f"\nSuccess! Appended {added_count} queries to {grouped_path}.")
    print("IMPORTANT: The 'target_intent_id' for all new queries has been defaulted to 0.")
    print("If these APIs have multiple intents, please open test_queries_grouped.json and manually update the target_intent_id!")

if __name__ == "__main__":
    main()
