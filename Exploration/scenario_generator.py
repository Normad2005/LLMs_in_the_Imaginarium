# === scenario_generator.py ===
import os
import sys

# 解決 Windows cp950 環境下 console 輸出 Unicode 字元崩潰問題
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

# ─── 專案根目錄（此腳本所在的 Exploration/ 的上一層）────────────────────────────
_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))  # .../Exploration
_PROJ_ROOT  = os.path.dirname(_THIS_DIR)                  # .../ (project root)
"""
根據每個 API 的 tool description，讓 LLM 分析並生成可能的使用情境 (Scenarios)。

使用情境的數量根據 API 複雜度自動決定

輸出格式 (scenarios.json)：
{
  "get_weather_forecast": {
    "usage_count": 2,
    "usages": [
      {
        "id": "A",
        "description": "Uses the service to retrieve the weather forecast for a specific city."
      },
      ...
    ]
  }
}
"""

import os.path
import sys
import re
import json
import time

# 確保無論從哪個目錄執行都能 import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from Exploration.my_llm import call_ollama


def _proj(rel: str) -> str:
    """將相對路徑轉換為以專案根目錄為基準的絕對路徑。"""
    return os.path.join(_PROJ_ROOT, rel)

# ─── 設定 ────────────────────────────────────────────────────────────────────
TOOL_DESC_PATH = _proj("tool_metadata/tool_description.json")
OUT_PATH       = _proj("results/scenarios.json")
MODEL_CKPT     = "gpt-oss:120b"   # 改成你想用的模型
TEMPERATURE    = 0.3
MAX_RETRIES    = 3
RETRY_DELAY    = 5.0

# ─── Prompt ──────────────────────────────────────────────────────────────────
SYSTEM_HINT = """\
You are an expert API analyst. Your job is to identify distinct usage patterns \
for a given API based on its description and parameters.\
"""

PROMPT_TEMPLATE = """\
You are analyzing an API to identify its distinct usage patterns (usages) in English.

API Name: {api_name}

API Description:
{api_description}

Required Parameters:
{required_params}

Optional Parameters:
{optional_params}

─────────────────────────────────────────────────────────────────────────────
TASK
─────────────────────────────────────────────────────────────────────────────
Identify all meaningfully DISTINCT ways a user might call or use this API.
Usages differ when:
  • Different subsets of parameters are needed (e.g., search-by-name vs. search-by-coordinates)
  • The user's intent or context is fundamentally different (e.g., comparing two entities vs. querying single entity status vs. overall leaderboard)
  • Mutually exclusive parameter groups lead to different query patterns

Rules:
  1. For SIMPLE APIs with few parameters or single functionality → produce 1–2 usages.
  2. For COMPLEX APIs with many optional parameters or multiple query modes → produce as many
     usages as genuinely distinct patterns exist based on parameter dependencies (no artificial upper limit).
  3. Do NOT create usages that are merely trivial variations (e.g., same pattern but a different value).
  4. All output text MUST be written in English.
  5. Focus on the actual API usage/functionality rather than human context or scenario (e.g., do NOT write "A hiker uses...", "A traveler wants to...", "A developer calls..."). Write the description directly starting with a verb (e.g., "Uses the service to locate...", "Retrieves the historical...", "Compare two different teams..."). Do NOT include prefixes like "Usage A (Hypothetical Scenario):" in the description.

─────────────────────────────────────────────────────────────────────────────
OUTPUT FORMAT  (respond with valid JSON ONLY, no extra text)
─────────────────────────────────────────────────────────────────────────────
{{
  "usages": [
    {{
      "id": "A",
      "description": "<Direct description of the usage/functionality in English, starting with a verb. Do NOT include prefix.>"
    }},
    ...
  ]
}}
"""

# ─── 輔助函數 ─────────────────────────────────────────────────────────────────

def format_params(param_list: list) -> str:
    """將參數 list 格式化成可讀的字串。"""
    if not param_list:
        return "  (none)"
    lines = []
    for p in param_list:
        name = p.get("name", "?")
        typ  = p.get("type", "?")
        desc = p.get("description", "")
        default = p.get("default", None)
        line = f"  - {name} ({typ}): {desc}"
        if default is not None:
            line += f"  [default: {default}]"
        lines.append(line)
    return "\n".join(lines)


def extract_json(text: str) -> dict | None:
    """從 LLM 回應中萃取 JSON 物件（處理 markdown code fence）。"""
    # 1. 嘗試直接解析
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2. 去掉 markdown fence
    fenced = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if fenced:
        try:
            return json.loads(fenced.group(1).strip())
        except Exception:
            pass

    # 3. 找第一個 { ... } 區塊
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        candidate = m.group(0)
        # 修補常見的 trailing comma 錯誤
        candidate = re.sub(r",\s*}", "}", candidate)
        candidate = re.sub(r",\s*\]", "]", candidate)
        try:
            return json.loads(candidate)
        except Exception:
            pass

    return None


def generate_scenarios_for_api(api_name: str, api_info: dict) -> dict | None:
    """
    呼叫 LLM 為單一 API 生成使用情境（usages）。
    成功時回傳 dict，失敗時回傳 None。
    """
    required = api_info.get("required_parameters", [])
    optional = api_info.get("optional_parameters", [])
    description = api_info.get("description", "No description available.")

    prompt = PROMPT_TEMPLATE.format(
        api_name=api_name,
        api_description=description,
        required_params=format_params(required),
        optional_params=format_params(optional),
    )
    full_prompt = SYSTEM_HINT + "\n\n" + prompt

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            raw = call_ollama(MODEL_CKPT, full_prompt, temperature=TEMPERATURE)
        except Exception as e:
            print(f"    [warn] call_ollama raised: {e}  (attempt {attempt}/{MAX_RETRIES})")
            time.sleep(RETRY_DELAY)
            continue

        parsed = extract_json(raw)
        if parsed and "usages" in parsed and isinstance(parsed["usages"], list):
            usages = parsed["usages"]
            # 補全缺失的 id 欄位，並清理 description 的格式
            for i, u in enumerate(usages):
                u_id = u.get("id", chr(ord("A") + i)).upper()
                u["id"] = u_id
                desc = u.get("description", "")
                
                # 移除可能不小心產生的 "Usage A (Hypothetical Scenario):" 首碼
                clean_desc = re.sub(r"^Usage\s+[A-Z]\s*\(Hypothetical\s+Scenario\):\s*", "", desc, flags=re.IGNORECASE).strip()
                # 將 "A hiker uses the service to..." 轉換成以動詞 "uses the service to..." 開頭
                clean_desc = re.sub(
                    r"^(?:A\s+)?(?:user|hiker|traveler|developer|enthusiast|client|application|reader|player|investor|borrower|homeowner|homebuyer|organizer|coder|gamer|fan|someone|people)\s+(?:simply\s+)?(?:uses\s+the\s+service\s+to|calls\s+the\s+API\s+to|invokes\s+the\s+API\s+to|calls\s+the\s+endpoint\s+to|uses\s+the\s+API\s+to|calls\s+the\s+API|invokes\s+the\s+API)\s*",
                    "uses the service to ",
                    clean_desc,
                    flags=re.IGNORECASE
                )
                
                # 確保第一個字母大寫
                if clean_desc:
                    clean_desc = clean_desc[0].upper() + clean_desc[1:]
                u["description"] = clean_desc
            return {
                "usage_count": len(usages),
                "usages": usages
            }
        else:
            print(f"    [warn] Could not parse JSON from response (attempt {attempt}/{MAX_RETRIES})")
            print(f"    Raw snippet: {raw[:200]!r}")
            time.sleep(RETRY_DELAY)

    return None


# ─── 主程式 ───────────────────────────────────────────────────────────────────

def main(
    tool_desc_path: str = TOOL_DESC_PATH,
    out_path: str = OUT_PATH,
    model_ckpt: str = MODEL_CKPT,
    resume: bool = True,
):
    """
    Args:
        tool_desc_path: tool_description.json 路徑
        out_path: 輸出 JSON 路徑
        model_ckpt: Ollama 模型名稱
        resume: 若 True，跳過已處理的 API（支援中斷續跑）
    """
    global MODEL_CKPT
    MODEL_CKPT = model_ckpt

    # 讀入工具描述
    with open(tool_desc_path, "r", encoding="utf-8") as f:
        tool_desc: dict = json.load(f)

    total = len(tool_desc)
    print(f"[OK] Loaded {total} APIs from {tool_desc_path}")

    # 若輸出檔已存在且 resume=True，先讀入以便斷點續跑
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if resume and os.path.exists(out_path):
        try:
            with open(out_path, "r", encoding="utf-8") as f:
                results: dict = json.load(f)
            # 檢查是否為舊格式，若是，則清除重新生成
            if results:
                first_key = list(results.keys())[0]
                # 如果是包含舊格式欄位的 JSON，或是含有舊 prefix 的，強制重新生成
                if "scenarios" in results[first_key] or any("Usage " in u.get("description", "") for u in results[first_key].get("usages", [])):
                    print("[Warn] Found old format in output file. Discarding to restart with new format.")
                    results = {}
                else:
                    print(f"[Resume] Resuming — already processed: {len(results)}/{total}")
            else:
                results = {}
        except Exception:
            results = {}
    else:
        results = {}

    # 依序處理每個 API
    for idx, (api_name, api_info) in enumerate(tool_desc.items(), start=1):
        if resume and api_name in results:
            print(f"[{idx:02d}/{total}] [Skip] {api_name} — skipped (already done)")
            continue

        print(f"\n[{idx:02d}/{total}] [Run] Processing: {api_name}")
        result = generate_scenarios_for_api(api_name, api_info)

        if result is None:
            print(f"  [Error] Failed to generate scenarios for {api_name}")
            results[api_name] = {
                "usage_count": 0,
                "usages": [],
                "error": "LLM generation failed after max retries"
            }
        else:
            n = result["usage_count"]
            print(f"  [OK] Generated {n} usage(s):")
            for u in result["usages"]:
                print(f"     {u.get('description','')}")
            results[api_name] = result

        # 每處理完一個 API 就立刻存檔（防止崩潰遺失進度）
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    # ─── 完成後印出統計 ───────────────────────────────────────────────────────
    total_usages = sum(v.get("usage_count", 0) for v in results.values())
    failed = [k for k, v in results.items() if v.get("usage_count", 0) == 0]

    print("\n" + "="*60)
    print(f"[Done] Done! Processed {len(results)} APIs.")
    print(f"[Stats] Total usages generated: {total_usages}")
    print(f"   Average per API: {total_usages / max(len(results),1):.1f}")
    if failed:
        print(f"[Warn] Failed APIs ({len(failed)}): {', '.join(failed)}")
    print(f"[Save] Results saved to: {out_path}")
    print("="*60)


# ─── CLI 入口 ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate usage scenarios for each API based on tool descriptions."
    )
    parser.add_argument(
        "--tool_desc_path", type=str, default=TOOL_DESC_PATH,
        help=f"Path to tool_description.json (default: {TOOL_DESC_PATH})"
    )
    parser.add_argument(
        "--out_path", type=str, default=OUT_PATH,
        help=f"Output JSON path (default: {OUT_PATH})"
    )
    parser.add_argument(
        "--model_ckpt", type=str, default=MODEL_CKPT,
        help=f"Ollama model checkpoint (default: {MODEL_CKPT})"
    )
    parser.add_argument(
        "--no_resume", action="store_true",
        help="Start from scratch, ignoring any existing output file."
    )

    args = parser.parse_args()
    main(
        tool_desc_path=args.tool_desc_path,
        out_path=args.out_path,
        model_ckpt=args.model_ckpt,
        resume=not args.no_resume,
    )
