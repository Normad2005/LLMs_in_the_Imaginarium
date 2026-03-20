# === tool_erratum_builder.py ===
"""
輸入：
  - intent_clusters.json  (intent_clustering.py 的輸出)
  - tool_data_train.json  (postprocessing.py 的輸出，成功案例)
  - tool_description.json

輸出：Tool Errata Repository
{
  "api_name": {
    "units": [
      {
        "scenario_id": 0,
        "name": "...",
        "scenario": "...",
        "tool_errata": ["...", "..."],
        "examples": [{ "query": "...", "action": "...", "action_input": {...} }]
      }
    ]
  }
}

Session 優先順序：
  1. 有修正過程的 session（第一輪失敗、後來成功）← 最能揭示約束條件
  2. 純失敗 session（全程失敗）← 顯示錯誤模式
  3. 純成功 session（第一輪就成功）← 確認正確用法
空情境：errata 純粹由 API Description 生成，examples 為空。
"""

import os
import re
import json
from my_llm import call_ollama

# ---------- config ----------
CLUSTER_PATH   = "results/intent_clusters.json"
TRAIN_PATH     = "results/ste/gpt_tool_data_train.json"
TOOL_DESC_PATH = "tool_metadata/tool_description.json"
OUT_PATH       = "results/tool_errata_repository.json"
MODEL_CKPT     = "gpt-oss:120b"

MAX_CORRECTION_SESSIONS = 3   # 最多送幾條「有修正過程」的 session
MAX_FAIL_SESSIONS       = 2   # 最多補幾條「純失敗」的 session
MAX_SUCC_SESSIONS       = 2   # 最多補幾條「純成功」的 session
MAX_EXAMPLES            = 3   # 每個 Unit 保留幾筆 examples
OBS_TRUNCATE            = 300 # observation 截斷長度


# ---------- session 分類 ----------
def has_correction(session: dict) -> bool:
    """第一輪失敗（有 error observation）但最終成功的 session。"""
    chains = session.get("chains", [])
    if len(chains) < 2:
        return False
    first_obs = str(chains[0].get("observation", "")).lower()
    has_error = "error" in first_obs or "invalid" in first_obs or "missing" in first_obs
    return has_error and session.get("reflection", "No") == "Yes"

def is_pure_fail(session: dict) -> bool:
    return session.get("reflection", "No") == "No"

def is_pure_success(session: dict) -> bool:
    chains = session.get("chains", [])
    if not chains:
        return False
    first_obs = str(chains[0].get("observation", "")).lower()
    no_error = "error" not in first_obs and "invalid" not in first_obs
    return no_error and session.get("reflection", "No") == "Yes"


# ---------- 修正軌跡格式化 ----------
def format_correction_trajectory(session: dict) -> str:
    """
    完整呈現一個 session 的修正過程。
    重點：每輪的 action_input → observation（錯誤訊息）→ 下一輪的修正。
    """
    lines = [f"Query: {session.get('query', '')}"]
    chains = session.get("chains", [])

    for i, c in enumerate(chains):
        parsed      = c.get("parsed", {})
        obs         = str(c.get("observation", ""))
        action_input= parsed.get("action_input", "")
        thought     = parsed.get("thought", "")
        finish      = parsed.get("finish", False)

        if finish:
            final_ans = parsed.get("final_ans", "")
            lines.append(f"  [Turn {i}] → Final Answer: {str(final_ans)[:100]}")
            break

        # 截斷但保留錯誤關鍵字完整
        obs_display = obs[:OBS_TRUNCATE] + ("..." if len(obs) > OBS_TRUNCATE else "")

        lines.append(
            f"  [Turn {i}]\n"
            f"    Thought: {str(thought)[:120]}\n"
            f"    Action Input: {str(action_input)[:200]}\n"
            f"    Observation: {obs_display}"
        )

    result = session.get("reflection", "No")
    lines.append(f"  [Result] reflection={result}")
    return "\n".join(lines)

def format_simple_session(session: dict) -> str:
    """純成功或純失敗 session，只取第一輪。"""
    chains = session.get("chains", [])
    query  = session.get("query", "")
    if not chains:
        return f"Query: {query}\n  (no chains)"

    c            = chains[0]
    parsed       = c.get("parsed", {})
    obs          = str(c.get("observation", ""))[:OBS_TRUNCATE]
    action_input = parsed.get("action_input", "")

    return (
        f"Query: {query}\n"
        f"  Action Input: {str(action_input)[:200]}\n"
        f"  Observation: {obs}"
    )


# ---------- API 參數結構化抽取 ----------
def format_params(api_desc: dict) -> tuple:
    """
    從 api_desc 抽出 required / optional 參數，
    回傳兩個易讀字串供 prompt 使用。
    """
    def fmt(params: list) -> str:
        if not params:
            return "none"
        lines = []
        for p in params:
            name  = p.get("name", "?")
            ptype = p.get("type", "")
            desc  = p.get("description", "")
            dflt  = p.get("default", None)
            line  = f"  - {name} ({ptype}): {desc}"
            if dflt is not None:
                line += f"  [default: {dflt}]"
            lines.append(line)
        return "\n".join(lines)

    required = fmt(api_desc.get("required_parameters", []))
    optional = fmt(api_desc.get("optional_parameters", []))
    return required, optional


# ---------- examples ----------
def pick_examples(api_name: str, scenario_queries: list,
                  train_by_api: dict, n: int) -> list:
    candidates = train_by_api.get(api_name, [])
    q_set      = set(scenario_queries)
    priority   = [ex for ex in candidates if ex.get("query") in q_set]
    rest       = [ex for ex in candidates if ex.get("query") not in q_set]
    picked     = (priority + rest)[:n]
    return [
        {
            "query":        ex.get("query", ""),
            "action":       ex.get("action", api_name),
            "action_input": ex.get("action_input", {}),
        }
        for ex in picked
    ]


# ---------- errata 解析 ----------
def parse_errata(resp: str) -> list:
    errata    = []
    in_errata = False
    for line in resp.splitlines():
        if re.match(r"Tool\s+Errata\s*:", line, re.IGNORECASE):
            in_errata = True
            continue
        if in_errata:
            if re.match(r"[A-Z][a-z]+\s*:", line):
                break
            bullet = re.match(r"^\s*[-*•]\s*(.+)", line)
            if bullet:
                rule = bullet.group(1).strip()
                if rule:
                    errata.append(rule)
    return errata


# ---------- prompts ----------
# 使用 __KEY__ 形式的 placeholder，避免 json.dumps 的 {} 被 .format() 誤解析
# 統一由 build_prompt() 做字串替換

PROMPT_WITH_SESSIONS = """\
You are distilling API usage knowledge into concise parameter rules for a small language model.

API name: __API_NAME__
API description:
__API_DESC__

Scenario: __SCENARIO_NAME__
Scenario description: __SCENARIO_DESC__
Key parameters for this scenario: __KEY_PARAMS__

--- Sessions with CORRECTION process (most informative: shows what failed and how it was fixed) ---
__CORRECTION_BLOCK__

--- Pure FAILED sessions (shows common mistakes) ---
__FAIL_BLOCK__

--- Pure SUCCESSFUL sessions (confirms correct usage) ---
__SUCCESS_BLOCK__

Task:
Write the minimal set of rules a model needs to correctly call this API in THIS scenario.
Think of it as replacing the API description with a pre-digested, scenario-specific cheat sheet.

Each rule must answer one of:
- What parameters are needed and what value/format must they take?
- What constraint is NOT obvious from a casual reading of the API description \
  (revealed by failures or corrections above)?

Rules for writing rules:
- Maximum 3 rules. If you only need 1 or 2, that is fine.
- If multiple observations point to the same constraint, write it ONCE.
- Merge related constraints into a single sentence rather than splitting them.
- Be concrete: prefer "states must be uppercase abbreviations e.g. NY,FL" \
  over "states must be in the correct format".

Do NOT include:
- Rules about ReAct reasoning format (Thought / Action / Observation structure)
- Rules about which API to select
- Restatements of what the API does or its general purpose
- Redundant rules that repeat the same constraint in different words

Output format (follow exactly, no other text):
Tool Errata:
- <rule 1>
- <rule 2 if needed>
- <rule 3 if needed>
"""

PROMPT_EMPTY_SCENARIO = """\
You are distilling API usage knowledge into concise parameter rules for a small language model.

API name: __API_NAME__
API description:
__API_DESC__

Scenario: __SCENARIO_NAME__
Scenario description: __SCENARIO_DESC__
Key parameters for this scenario: __KEY_PARAMS__

No usage sessions are available for this scenario.
Based on the API description alone, write the minimal rules a model needs \
to correctly call this API in THIS scenario.

Rules for writing rules:
- Maximum 3 rules. If you only need 1 or 2, that is fine.
- Merge related constraints into a single sentence rather than splitting them.
- Be concrete about parameter names, types, and formats.

Do NOT include:
- Rules about ReAct reasoning format
- Rules about which API to select
- Restatements of what the API does

Output format (follow exactly, no other text):
Tool Errata:
- <rule 1>
- <rule 2 if needed>
- <rule 3 if needed>
"""


def build_prompt(template: str, **kwargs) -> str:
    """
    用 str.replace() 逐一替換 __KEY__ 形式的 placeholder。
    不使用 .format()，避免 json.dumps 輸出的大括號被誤解析。
    """
    prompt = template
    for key, value in kwargs.items():
        prompt = prompt.replace(f"__{key.upper()}__", str(value))
    return prompt


# ---------- main ----------
def main(
    cluster_path:   str = CLUSTER_PATH,
    train_path:     str = TRAIN_PATH,
    tool_desc_path: str = TOOL_DESC_PATH,
    out_path:       str = OUT_PATH,
    model_ckpt:     str = MODEL_CKPT,
):
    with open(cluster_path, "r", encoding="utf-8") as f:
        cluster_data = json.load(f)

    with open(train_path, "r", encoding="utf-8") as f:
        train_data = json.load(f)

    with open(tool_desc_path, "r", encoding="utf-8") as f:
        tool_desc = json.load(f)

    train_by_api: dict = {}
    for item in train_data:
        api = item.get("action", "")
        train_by_api.setdefault(api, []).append(item)

    repository = {}

    for api_name, api_data in cluster_data.items():
        print(f"\n===== {api_name} =====")
        scenarios = api_data.get("scenarios", [])
        if not scenarios:
            continue

        api_desc = tool_desc.get(api_name, {"description": "No description available."})
        units    = []

        for scenario in scenarios:
            sid         = scenario["scenario_id"]
            name        = scenario["name"]
            description = scenario["description"]
            key_params  = scenario.get("key_parameters", [])
            sessions    = scenario.get("sessions", [])
            is_empty    = len(sessions) == 0

            print(f"\n  Scenario {sid} [{name}]")
            print(f"  Description: {description}")
            print(f"  Sessions: {'⚠️  empty' if is_empty else len(sessions)}")

            api_desc_str = json.dumps(api_desc, indent=2, ensure_ascii=False)
            key_params_str = ", ".join(key_params) or "not specified"

            if is_empty:
                prompt = build_prompt(
                    PROMPT_EMPTY_SCENARIO,
                    api_name=api_name,
                    api_desc=api_desc_str,
                    scenario_name=name,
                    scenario_desc=description,
                    key_params=key_params_str,
                )
            else:
                # 分類 sessions
                correction_sessions = [s for s in sessions if has_correction(s)]
                fail_sessions       = [s for s in sessions if is_pure_fail(s)]
                success_sessions    = [s for s in sessions if is_pure_success(s)]

                print(f"  → correction={len(correction_sessions)}, "
                      f"pure_fail={len(fail_sessions)}, "
                      f"pure_success={len(success_sessions)}")

                correction_block = "\n\n".join(
                    format_correction_trajectory(s)
                    for s in correction_sessions[:MAX_CORRECTION_SESSIONS]
                ) or "None"

                fail_block = "\n\n".join(
                    format_simple_session(s)
                    for s in fail_sessions[:MAX_FAIL_SESSIONS]
                ) or "None"

                success_block = "\n\n".join(
                    format_simple_session(s)
                    for s in success_sessions[:MAX_SUCC_SESSIONS]
                ) or "None"

                prompt = build_prompt(
                    PROMPT_WITH_SESSIONS,
                    api_name=api_name,
                    api_desc=api_desc_str,
                    scenario_name=name,
                    scenario_desc=description,
                    key_params=key_params_str,
                    correction_block=correction_block,
                    fail_block=fail_block,
                    success_block=success_block,
                )

            # LLM 生成 errata
            try:
                resp   = call_ollama(model_ckpt, prompt, temperature=0)
                errata = parse_errata(resp)
            except Exception as e:
                print(f"  [ERROR] LLM call failed: {e}")
                errata = []

            if not errata:
                errata = ["Follow the API description carefully."]

            # examples
            if is_empty:
                examples = []
            else:
                scenario_queries = [s.get("query", "") for s in sessions]
                examples = pick_examples(api_name, scenario_queries, train_by_api, MAX_EXAMPLES)

            # 印出產出的規則
            print(f"  Tool Errata ({len(errata)} rules):")
            for rule in errata:
                print(f"    - {rule}")
            print(f"  Examples: {len(examples)}")

            units.append({
                "scenario_id": sid,
                "name":        name,
                "scenario":    description,
                "tool_errata": errata,
                "examples":    examples,
            })

        repository[api_name] = {"units": units}

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(repository, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Saved Tool Errata Repository to {out_path}")


if __name__ == "__main__":
    main()