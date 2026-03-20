# === demo_retrieve.py ===
"""
跨 API 檢索版本。

與原版差異：
  原版：先鎖定 api_name，在該 API 的訓練資料裡找最相似 query
  新版：所有 API 的訓練資料合併成一個 pool，直接跨 API 找最相似 query
        demo 可能來自不同 API，讓模型從中學習正確的參數填寫方式

輸出：每筆 test example 新增 "demo" 欄位，格式與原版相同：
  [{ "query": "...", "action": "...", "action_input": {...} }, ...]
"""

import os
import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util

def main(
    train_path="results/ste/gpt_tool_data_train.json",
    test_path="tool_metadata/tool_test.json",
    save_path="tool_metadata/tool_test_with_demo.json",
    num_examples_retrieve=8,
    model_name="sentence-transformers/paraphrase-mpnet-base-v2",
):
    # === 1. 載入資料 ===
    with open(train_path, "r", encoding="utf-8") as f:
        train_data = json.load(f)
    with open(test_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    print(f"✅ Loaded {len(train_data)} training examples.")
    print(f"✅ Loaded {len(test_data)} APIs in test set.")

    # === 2. 去重（同 query 只保留一筆）===
    seen_queries = set()
    train_items, train_queries = [], []
    for item in train_data:
        q = item["query"]
        if q not in seen_queries:
            seen_queries.add(q)
            train_items.append(item)
            train_queries.append(q)

    print(f"✅ Deduplicated to {len(train_items)} unique training queries.")

    # === 3. 初始化嵌入模型 ===
    print(f"🔧 Loading embedding model: {model_name}")
    embed_model = SentenceTransformer(model_name)

    # === 4. 對所有訓練 query 做 embedding（跨 API 合併）===
    print("🗂️  Encoding all training queries...")
    train_embeddings = embed_model.encode(train_queries, convert_to_tensor=True)
    print(f"  → Encoded {len(train_queries)} queries.")

    # === 5. 為每筆 test example 跨 API 檢索最相似 demo ===
    for api_name, examples in test_data.items():
        print(f"\n🔍 Processing API: {api_name} ({len(examples)} examples)")

        for i in tqdm(range(len(examples))):
            query    = examples[i]["query"]
            test_emb = embed_model.encode([query], convert_to_tensor=True)
            scores   = util.cos_sim(test_emb, train_embeddings)[0]

            # 取 Top-K（跨所有 API）
            top_idx  = scores.argsort(descending=True)[:num_examples_retrieve]
            demo_list = [train_items[int(idx)] for idx in top_idx]

            # 精簡 demo 結構
            examples[i]["demo"] = [
                {
                    "query":        d["query"],
                    "action":       d["action"],
                    "action_input": d["action_input"],
                }
                for d in demo_list
            ]

        test_data[api_name] = examples

    # === 6. 儲存輸出 ===
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"\n📦 Saved cross-API demo-augmented test set to: {save_path}")


if __name__ == "__main__":
    main()