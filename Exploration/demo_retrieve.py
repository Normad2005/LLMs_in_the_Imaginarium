# === demo_retrieve.py ===
import json
import os
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util

def main(
    train_path="results/ste/tool_data_train.json",
    test_path="tool_metadata/tool_test.json",
    save_path="tool_metadata/tool_test_with_demo.json",
    num_examples_retrieve=8,
    model_name="sentence-transformers/paraphrase-mpnet-base-v2"
):


    # === 1. 載入資料 ===
    with open(train_path, "r", encoding="utf-8") as f:
        train_data = json.load(f)
    with open(test_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    print(f"✅ Loaded {len(train_data)} training examples.")
    print(f"✅ Loaded {len(test_data)} APIs in test set.")

    # === 2. 整理訓練資料 ===
    train_by_api = {}
    for item in train_data:
        api = item["action"]
        train_by_api.setdefault(api, []).append(item)

    # === 3. 初始化嵌入模型 ===
    print(f"🔧 Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)

    # === 4. 預先生成訓練 query 向量 ===
    train_embeddings_by_api = {}
    for api, items in train_by_api.items():
        queries = [ex["query"] for ex in items]
        embeddings = model.encode(queries, convert_to_tensor=True)
        train_embeddings_by_api[api] = {"items": items, "embeddings": embeddings}
        print(f"  → Encoded {len(items)} examples for API '{api}'")

    # === 5. 為每個測試樣本檢索相似 demo ===
    for api_name in test_data:
        examples = test_data[api_name]
        print(f"\n🔍 Processing API: {api_name} ({len(examples)} examples)")

        # 若該 API 在訓練集中不存在，則跳過
        if api_name not in train_embeddings_by_api:
            print(f"⚠️ No training data for API '{api_name}', skipping.")
            continue

        train_bank = train_embeddings_by_api[api_name]["items"]
        train_embs = train_embeddings_by_api[api_name]["embeddings"]

        for i in tqdm(range(len(examples))):
            query = examples[i]["query"]
            test_emb = model.encode([query], convert_to_tensor=True)
            cosine_scores = util.cos_sim(test_emb, train_embs)[0]

            # 取前 num_examples_retrieve 筆
            top_idx = cosine_scores.argsort(descending=True)[:num_examples_retrieve]
            demo_list = [train_bank[int(idx)] for idx in top_idx]

            # 精簡 demo 結構
            demos = [
                {
                    "query": d["query"],
                    "action": d["action"],
                    "action_input": d["action_input"]
                }
                for d in demo_list
            ]
            examples[i]["demo"] = demos

        test_data[api_name] = examples

    # === 6. 儲存輸出 ===
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"\n📦 Saved demo-augmented test set to: {save_path}")


if __name__ == "__main__":
    main()
