import os
import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util

def main():
    train_path = "results/ste/gpt_tool_data_train_35_APIs.json"
    test_path = "tool_metadata/test_queries_simple.json"
    save_path = "tool_metadata/test_queries_with_demo_simple_APIs.json"
    # 比照 STE 論文設定為 8 個範例
    num_examples_retrieve = 8
    model_name = "sentence-transformers/paraphrase-mpnet-base-v2"

    print(f"Loading training data from {train_path}...")
    with open(train_path, "r", encoding="utf-8") as f:
        train_data = json.load(f)
        
    print(f"Loading test queries from {test_path}...")
    with open(test_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    print(f"Loaded {len(train_data)} training examples.")
    print(f"Loaded {len(test_data)} simple APIs.")

    # 對訓練集的 Query 進行去重
    seen_queries = set()
    train_items, train_queries = [], []
    for item in train_data:
        q = item["query"]
        if q not in seen_queries:
            seen_queries.add(q)
            train_items.append(item)
            train_queries.append(q)

    print(f"Deduplicated to {len(train_items)} unique training queries.")

    print(f"Loading embedding model: {model_name}")
    embed_model = SentenceTransformer(model_name)

    print("Encoding all training queries...")
    train_embeddings = embed_model.encode(train_queries, convert_to_tensor=True)
    print(f"  → Encoded {len(train_queries)} queries.")

    # 針對每一題尋找最相似的 8 個 Demo
    for api_name, examples in test_data.items():
        print(f"\nProcessing API: {api_name} ({len(examples)} examples)")

        for i in tqdm(range(len(examples))):
            query    = examples[i]["query"]
            test_emb = embed_model.encode([query], convert_to_tensor=True)
            scores   = util.cos_sim(test_emb, train_embeddings)[0]

            top_idx  = scores.argsort(descending=True)[:num_examples_retrieve]
            demo_list = [train_items[int(idx)] for idx in top_idx]

            examples[i]["demo"] = [
                {
                    "query":        d["query"],
                    "action":       d.get("action", api_name),
                    "action_input": d.get("action_input", {}),
                }
                for d in demo_list
            ]

        test_data[api_name] = examples

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved demo-augmented test set to: {save_path}")

if __name__ == "__main__":
    main()
