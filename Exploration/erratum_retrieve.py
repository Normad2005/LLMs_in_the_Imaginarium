# === erratum_retrieve.py ===
"""
離線階段：把所有 Unit 的 Scenario 做 embedding，建立檢索索引。
推論階段：
  1. user query → 假想情境（一次 LLM call）
  2. 假想情境 embedding → 比對所有 Unit 的 Scenario embedding（跨 API）
  3. 取 Top-K Units，寫入 test JSON 的 "erratum" 欄位

輸出格式（每筆 test example 新增欄位）：
{
  "query": "...",
  "erratum": [
    {
      "api_name":    "...",
      "scenario":    "...",
      "tool_errata": ["...", "..."],
      "examples":    [...]
    }
  ]
}
"""

import os
import json
from tqdm import tqdm
from sentence_transformers import SentenceTransformer, util
from my_llm import call_ollama

# ---------- config ----------
REPOSITORY_PATH = "results/tool_errata_repository.json"
TEST_PATH       = "tool_metadata/tool_test.json"
OUT_PATH        = "tool_metadata/tool_test_with_erratum.json"
EMBED_MODEL     = "sentence-transformers/paraphrase-mpnet-base-v2"
HYPO_MODEL      = "gpt-oss:120b"   # 生成假想情境用的模型
TOP_K           = 2                # 每個 query 檢索幾個 Unit


# ---------- hypothetical scenario generation ----------
HYPO_PROMPT = """\
Given the following user query, write ONE sentence describing the abstract usage scenario \
(what kind of API operation the user needs, without mentioning specific values).

User Query: {query}

Output only the scenario sentence, nothing else.
Scenario:"""


def generate_hypothetical_scenario(query: str, model_ckpt: str) -> str:
    prompt = HYPO_PROMPT.format(query=query)
    try:
        resp = call_ollama(model_ckpt, prompt, temperature=0)
        # 取第一行，去掉可能殘留的 "Scenario:" 前綴
        line = resp.strip().splitlines()[0]
        line = line.removeprefix("Scenario:").strip()
        return line if line else query   # fallback: 直接用 query
    except Exception:
        return query


# ---------- build index ----------
def build_scenario_index(repository: dict, embed_model: SentenceTransformer) -> tuple:
    """
    把所有 Unit 的 Scenario 做 embedding。
    回傳：
      unit_list  - list of { api_name, cluster_id, scenario, tool_errata, examples }
      embeddings - tensor, shape (N, dim)
    """
    unit_list = []
    scenarios = []

    for api_name, api_data in repository.items():
        for unit in api_data.get("units", []):
            unit_list.append({
                "api_name":    api_name,
                "scenario_id": unit.get("scenario_id", 0),
                "name":        unit.get("name", ""),
                "scenario":    unit.get("scenario", ""),
                "tool_errata": unit.get("tool_errata", []),
                "examples":    unit.get("examples", []),
            })
            scenarios.append(unit.get("scenario", ""))

    print(f"  → Encoding {len(scenarios)} scenarios...")
    embeddings = embed_model.encode(scenarios, convert_to_tensor=True)
    return unit_list, embeddings


# ---------- retrieve ----------
def retrieve_top_k(
    hypo_scenario: str,
    unit_list: list,
    unit_embeddings,
    embed_model: SentenceTransformer,
    top_k: int,
) -> list:
    query_emb = embed_model.encode([hypo_scenario], convert_to_tensor=True)
    scores    = util.cos_sim(query_emb, unit_embeddings)[0]
    top_idx   = scores.argsort(descending=True)[:top_k]
    return [unit_list[int(i)] for i in top_idx]


# ---------- main ----------
def main(
    repository_path: str = REPOSITORY_PATH,
    test_path:       str = TEST_PATH,
    out_path:        str = OUT_PATH,
    embed_model_name: str = EMBED_MODEL,
    hypo_model:      str = HYPO_MODEL,
    top_k:           int = TOP_K,
):
    print(f"📂 Loading repository: {repository_path}")
    with open(repository_path, "r", encoding="utf-8") as f:
        repository = json.load(f)

    print(f"📂 Loading test data:   {test_path}")
    with open(test_path, "r", encoding="utf-8") as f:
        test_data = json.load(f)

    print(f"🔧 Loading embedding model: {embed_model_name}")
    embed_model = SentenceTransformer(embed_model_name)

    # 建立全域 Scenario index（跨所有 API）
    print("🗂️  Building scenario index...")
    unit_list, unit_embeddings = build_scenario_index(repository, embed_model)
    print(f"  → Index size: {len(unit_list)} units")

    # 為每筆 test example 做檢索
    for api_name, examples in test_data.items():
        print(f"\n🔍 Processing API: {api_name} ({len(examples)} examples)")

        for i in tqdm(range(len(examples))):
            query = examples[i]["query"]

            # Step 1: 生成假想情境
            hypo = generate_hypothetical_scenario(query, hypo_model)

            # Step 2: 檢索 Top-K Units（跨所有 API）
            top_units = retrieve_top_k(hypo, unit_list, unit_embeddings, embed_model, top_k)

            # Step 3: 寫入結果（只保留需要的欄位）
            examples[i]["erratum"] = [
                {
                    "api_name":    u["api_name"],
                    "scenario":    u["scenario"],
                    "tool_errata": u["tool_errata"],
                    "examples":    u["examples"],
                }
                for u in top_units
            ]
            examples[i]["hypo_scenario"] = hypo   # 方便 debug

        test_data[api_name] = examples

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved erratum-augmented test set to {out_path}")


if __name__ == "__main__":
    main()