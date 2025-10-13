import os
import json
import numpy as np
import requests
from tqdm import tqdm
from cluster import load_trials, cluster_and_select_medoid, embed_texts

# === Llama3 接口設定 ===
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

VERBOSE = True

# === 調用 Llama3 產生語意規則 ===
def generate_semantic_rule(cluster, model=OLLAMA_MODEL):
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

Rule (desired): If the query mentions a day of the week (e.g., Monday, Friday), resolve it relative to today's date and use the correct calendar date when calling the forecast API.
"""

    trials_text = []
    for t in cluster:
        trials_text.append(
            f'Q: "{t["query"]}" | API: {t["api"]} | args: {json.dumps(t.get("args", {}))} | success: {t.get("success", False)}'
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

    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except Exception as e:
        return f"[ERROR calling model: {e}]"

# === Main Function ===
def main(output_path="semantic_rules.json"):
    # 1️⃣ 讀取 trials
    trials = load_trials()  # 從 embedding_cluster.py
    if not trials:
        print("[Main] No trials loaded.")
        return

    print(f"[Main] Loaded {len(trials)} trials.")

    # 2️⃣ Embedding
    print("[Main] Embedding all trials (this will call OpenAI API)...")
    queries = [t["query"] for t in trials]
    embeddings = np.array(embed_texts(queries))

    # 3️⃣ 聚類 + 選 medoid
    print("[Main] Clustering and selecting medoids...")
    selected_demos = cluster_and_select_medoid(trials, embeddings, do_template=False)

    # 將每個代表放入 cluster list，保持舊 semantic_generator 格式
    clusters = [[t] for t in selected_demos]

    # 4️⃣ 生成語意規則
    results = {}
    for idx, cluster in enumerate(tqdm(clusters, desc="Generating rules")):
        rule = generate_semantic_rule(cluster)
        examples = [t["query"] for t in cluster]
        results[f"cluster_{idx+1}"] = {"rule": rule, "examples": examples}

    # 5️⃣ 儲存結果
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Semantic rules saved to {output_path}")


if __name__ == "__main__":
    main()
