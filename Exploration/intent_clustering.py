# === intent_clustering.py ===
"""
流程：
  1. LLM 閱讀 API Description，直接定義 N 個使用情境
     （每個情境含：id, name, description, key_parameters）
  2. 若只有一個情境，所有 sessions 直接歸入，不做 embedding 比對
  3. 若多個情境，對每個 session 抽取第一個非空 thought（fallback: query），
     用 embedding 比對情境 description，分配到最相似的情境
  4. 沒有 session 對應的情境保留（空情境，errata 由 API Description 生成）

輸出：
{
  "api_name": {
    "scenarios": [
      {
        "scenario_id": 0,
        "name": "Head-to-Head Query",
        "description": "當用戶查詢兩支球隊的歷史對戰記錄時",
        "key_parameters": ["first_team", "second_team"],
        "sessions": [ ... ]   # 可為空 list
      }
    ]
  }
}
"""

import os
import re
import json
import numpy as np
from sentence_transformers import SentenceTransformer, util
from my_llm import call_ollama

# ---------- config ----------
STE_DATA_PATH  = "results/ste/gpt_20251208-205418.json"
TOOL_DESC_PATH = "tool_metadata/tool_description.json"
OUT_PATH       = "results/intent_clusters.json"
EMBED_MODEL    = "sentence-transformers/paraphrase-mpnet-base-v2"
LLM_MODEL      = "gpt-oss:120b"
MAX_SCENARIOS  = 6  # LLM 最多定義幾個情境


# ---------- Step 1: LLM 定義情境 ----------
SCENARIO_PROMPT = """\
You are analyzing an API to identify its distinct usage scenarios.

API name: {api_name}

API description:
{api_description}

Task:
Identify the fundamentally different ways a user might call this API.
"Fundamentally different" means the core PURPOSE or the primary parameter GROUP
changes between scenarios — not just whether optional/pagination parameters are filled.

Rules:
- If all calls to this API serve the same core purpose, output exactly 1 scenario.
- Do NOT split scenarios based on different values of the same parameter
  (e.g., different city names for a weather API is NOT a different scenario).
- Do NOT create a separate scenario just for default usage, pagination, or
  optional formatting parameters — fold these into the relevant scenario's rules instead.
- Only split when the user's INTENT is different and requires a clearly distinct
  parameter group (e.g., searching by location vs. searching by category).
- Maximum {max_scenarios} scenarios.

Output valid JSON only, no explanation, no markdown.
Format:
[
  {{
    "scenario_id": 0,
    "name": "<short English name>",
    "description": "<one sentence describing when this scenario applies>",
    "key_parameters": ["<param1>", "<param2>"]
  }}
]
"""


def llm_define_scenarios(api_name: str, api_desc: dict, model_ckpt: str) -> list:
    prompt = SCENARIO_PROMPT.format(
        api_name=api_name,
        api_description=json.dumps(api_desc, indent=2, ensure_ascii=False),
        max_scenarios=MAX_SCENARIOS,
    )
    try:
        resp = call_ollama(model_ckpt, prompt, temperature=0).strip()

        # 抽出 JSON array
        m = re.search(r"\[[\s\S]*\]", resp)
        if not m:
            raise ValueError("No JSON array found in response")

        scenarios = json.loads(m.group(0))

        # 基本格式驗證與補全
        cleaned = []
        for i, s in enumerate(scenarios):
            cleaned.append({
                "scenario_id":    i,
                "name":           s.get("name", f"Scenario {i}"),
                "description":    s.get("description", ""),
                "key_parameters": s.get("key_parameters", []),
                "sessions":       [],
            })
        return cleaned

    except Exception as e:
        print(f"    [WARN] LLM scenario definition failed: {e}")
        # Fallback：單一情境
        return [{
            "scenario_id":    0,
            "name":           "Default Usage",
            "description":    f"General usage of the {api_name} API",
            "key_parameters": [],
            "sessions":       [],
        }]


# ---------- Step 2: 抽取 session 的 thought ----------
def extract_thought(session: dict) -> str:
    """
    從 session 的 chains 裡抽取第一個非空的 thought。
    fallback：用 query。
    """
    for chain in session.get("chains", []):
        thought = chain.get("parsed", {}).get("thought", "").strip()
        if thought:
            return thought
    return session.get("query", "")


# ---------- Step 3: 分配 sessions 到情境 ----------
def assign_sessions(
    sessions: list,
    scenarios: list,
    embed_model: SentenceTransformer,
) -> list:
    """
    對每個 session 的 thought 做 embedding，
    比對所有情境的 description embedding，分配到最相似的情境。
    回傳填入 sessions 後的 scenarios。
    """
    if len(scenarios) == 1:
        # 只有一個情境，直接全部歸入
        scenarios[0]["sessions"] = sessions
        return scenarios

    # Encode 情境 descriptions
    desc_texts  = [s["description"] for s in scenarios]
    desc_embeddings = embed_model.encode(desc_texts, convert_to_tensor=True)

    # 對每個 session 分配
    for session in sessions:
        thought   = extract_thought(session)
        sess_emb  = embed_model.encode([thought], convert_to_tensor=True)
        scores    = util.cos_sim(sess_emb, desc_embeddings)[0]
        best_idx  = int(scores.argmax())
        scenarios[best_idx]["sessions"].append(session)

    return scenarios


# ---------- main ----------
def main(
    ste_data_path:    str = STE_DATA_PATH,
    tool_desc_path:   str = TOOL_DESC_PATH,
    out_path:         str = OUT_PATH,
    embed_model_name: str = EMBED_MODEL,
    llm_model:        str = LLM_MODEL,
):
    print(f"🔧 Loading embedding model: {embed_model_name}")
    embed_model = SentenceTransformer(embed_model_name)

    print(f"📂 Loading STE data:  {ste_data_path}")
    with open(ste_data_path, "r", encoding="utf-8") as f:
        ste_data = json.load(f)

    print(f"📂 Loading tool desc: {tool_desc_path}")
    with open(tool_desc_path, "r", encoding="utf-8") as f:
        tool_desc = json.load(f)

    result = {}

    for api_name, sessions in ste_data.items():
        print(f"\n===== {api_name}  ({len(sessions)} sessions) =====")

        api_desc = tool_desc.get(api_name, {"description": "No description available."})

        # Step 1: LLM 定義情境
        scenarios = llm_define_scenarios(api_name, api_desc, llm_model)
        print(f"    → {len(scenarios)} scenario(s) defined by LLM")
        for s in scenarios:
            print(f"      [{s['scenario_id']}] {s['name']}: {s['description']}")

        # Step 2 & 3: 分配 sessions
        if sessions:
            scenarios = assign_sessions(sessions, scenarios, embed_model)

        # 統計分配結果
        for s in scenarios:
            n = len(s["sessions"])
            status = "⚠️  empty" if n == 0 else f"{n} sessions"
            print(f"      [{s['scenario_id']}] {s['name']}: {status}")

        result[api_name] = {"scenarios": scenarios}

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved intent clusters to {out_path}")


if __name__ == "__main__":
    main()