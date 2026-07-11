# === ste_runner.py ===
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
import re
import json
from datetime import datetime
from utils import parse_response
from my_llm import chat_my, call_ollama
import textwrap

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from toolbench.tool_runner import get_rapidapi_response
from config.api_keys import RAPIDAPI_KEY

# === 全域設定 ===
RUN_ID = datetime.now().strftime("%Y%m%d-%H%M%S")

# === 載入 TOOL ===
with open("tool_metadata/tool_registry.json", "r", encoding="utf-8") as f:
    TOOL_REGISTRY = json.load(f)

with open("tool_metadata/tool_description.json", "r", encoding="utf-8") as f:
    TOOL_DESCRIPTION = json.load(f)

# === API 呼叫 ===
def run_tool(api_name: str, args: dict, truncate: int = 2048):
    if api_name not in TOOL_REGISTRY:
        return json.dumps({"error": f"❌ API '{api_name}' not found in registry."}, ensure_ascii=False)

    info = TOOL_REGISTRY[api_name]
    category = info["category"]
    tool_name = info["tool_name"]

    try:
        result = get_rapidapi_response({
            "category": category,
            "tool_name": tool_name,
            "api_name": api_name,
            "tool_input": json.dumps(args),
            "strip": "filter",
            "rapidapi_key": RAPIDAPI_KEY,
        })
    except Exception as e:
        result = {"error": str(e), "response": ""}

    result_str = json.dumps(result, ensure_ascii=False, indent=2)
    return result_str[:truncate]

# === 安全解析 JSON ===
def safe_json_loads(s: str):
    match = re.search(r"\{[\s\S]*\}", s)
    if not match:
        raise ValueError("No valid JSON found")
    json_str = match.group(0)
    json_str = re.sub(r"//.*?(?=\n|$)", "", json_str)
    json_str = re.sub(r"/\*[\s\S]*?\*/", "", json_str)
    json_str = re.sub(r",\s*}", "}", json_str)
    json_str = re.sub(r",\s*\]", "]", json_str)
    return json.loads(json_str)

# === LTM 格式化 ===
def LTM(queries, results):
    return [f"Query: {q} | Solved: {results[i]}" for i, q in enumerate(queries)]

# === STE 主程式 ===
def main(model_ckpt="gpt-oss:120b", num_episodes=10, num_stm_slots=2, max_turn=5, dir_write="results/ste/", resume_path=None):
    os.makedirs(dir_write, exist_ok=True)

    # === 載入 Prompt Template ===
    with open("prompts/prompt_explore.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()

    parts = prompt_template.split("=========")
    template_q = parts[0].strip()
    template_a = parts[1].strip()
    template_q_follow = parts[2].strip()
    template_a_follow = parts[3].strip()

    PAST_Q_MSG_pre = "Below are queries you have already explored and whether you successfully solved them with the API's help:"
    PAST_Q_MSG_post = "Based on these, try to explore queries that can help you understand the API further; avoid synthesizing queries that are too close to the existing ones."

    # === 決定輸出路徑 ===
    if resume_path is not None:
        # 直接續跑既有檔案，不產生新時間戳
        out_path = resume_path
        print(f"📂 Resuming from: {out_path}")
    elif model_ckpt == "gpt-oss:120b":
        out_path = os.path.join(dir_write, f"gpt_{RUN_ID}.json")
    elif model_ckpt == "llama3.1:8b-instruct-fp16":
        out_path = os.path.join(dir_write, f"llama_{RUN_ID}.json")
    else:
        out_path = os.path.join(dir_write, f"data_{RUN_ID}.json")

    # Load existing to resume if path exists
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            data_dict = json.load(f)
        print(f"✅ Loaded existing data: {list(data_dict.keys())}")
    else:
        data_dict = {}

    # === 從 RapidAPI Registry 載入所有 API ===
    api_list = [
        "search_exercises_by_name",
        "search_streaming_shows",
        "get_airport_delay_statistics",
    ]

    # === 每次只探索一個 API ===
    for api_name in api_list:
        if api_name not in data_dict:
            data_dict[api_name] = []
        
        print(f"\n===== Exploring {api_name} =====")

        api_info = f"API_name: {api_name}\nDescription:\n{json.dumps(TOOL_DESCRIPTION[api_name], indent=2, ensure_ascii=False)}"

        explored_queries, success_labels = [], []
        api_sessions = data_dict[api_name]

        # Resume from where we left off
        completed_eps = len(api_sessions) // num_stm_slots if num_stm_slots > 0 else len(api_sessions)
        ep_start = completed_eps

        if ep_start >= num_episodes:
            print(f"  ⏭ Skipping '{api_name}' (Already processed)")
            continue

        for ep in range(ep_start, num_episodes):
            print(f"\n    --- Episode {ep} ---")
            messages = [{"role": "system", "content": "You are a helpful assistant."}]

            # === Step 1: Query 生成 ===
            prompt_q = template_q.format(
                api_descriptions=api_info
            )
            if explored_queries:
                prompt_q_added_question = prompt_q + f"\n\n{PAST_Q_MSG_pre}\n" + "\n".join(LTM(explored_queries, success_labels)) + f"\n\n{PAST_Q_MSG_post}"+ "\n\nOnly output the query itself, nothing else.\nUser Query:"
            else:
                prompt_q_added_question = prompt_q + "\n\nOnly output the query itself, nothing else.\nUser Query:"

            query = ""
            while not query:
                response = chat_my(messages, prompt_q_added_question, max_tokens=1024, model=model_ckpt)[-1]["content"]
                query = response.strip()
            print(f"🧠 New Query: {query}")
            explored_queries.append(query)
            item = {"query": query, "chains": []}

            messages = messages + [
                {"role": "user", "content": prompt_q},
                {"role": "assistant", "content": query}
            ]

            # === Step 2: ReAct Chain ===
            prompt_a = template_a.format(api_descriptions=api_info, api_names=api_name, query=query)
            messages = chat_my(messages, prompt_a, stop="Observation:", max_tokens=1024, model=model_ckpt)
            temp = messages[-1]["content"]
            parsed = parse_response(temp, [api_name], api_info, proc_thought=True)

            for turn in range(max_turn):
                if not parsed["parse_successful"]:
                    obs = parsed["parse_error_msg"]
                elif parsed["finish"]:
                    item["chains"].append({
                        "step": turn,
                        "parsed": parsed,
                        "observation": "Final Answer"
                    })
                    break
                else:
                    try:
                        args = safe_json_loads(parsed["action_input"])
                        obs = run_tool(api_name, args)
                    except Exception as e:
                        obs = f"Error: {e}"

                item["chains"].append({
                    "step": turn,
                    "parsed": parsed,
                    "observation": obs
                })
                print(f"🔁 Turn {turn}: {parsed.get('action')} → {obs[:120]}")

                messages = chat_my(messages, "Observation: " + obs, stop="Observation:", max_tokens=1024, model=model_ckpt)
                temp = messages[-1]["content"]
                parsed = parse_response(temp, [api_name], api_info, proc_thought=True)

            # === Step 3: Reflection ===
            prompt_reflection = "Do you think you successfully fulfilled this query in the end? Respond with \"Yes\" or \"No\"."
            messages = chat_my(messages, prompt_reflection, stop="Observation:", max_tokens=1024, model=model_ckpt)
            res = messages[-1]["content"]
            successful = "Yes" if "Yes" in res else "No"
            print(f"✅ Reflection: {successful}")

            item["reflection"] = successful
            success_labels.append(successful)
            api_sessions.append(item)

            # === Step 4: Follow-up ===
            for f_idx in range(num_stm_slots - 1):
                print(f"\n      --- Follow-up #{f_idx + 1} ---")

                follow_q = template_q_follow.format(
                    api_descriptions=api_info
                )
                if explored_queries:
                    follow_q_added_question = follow_q + f"\n\n{PAST_Q_MSG_pre}\n" + "\n".join(LTM(explored_queries, success_labels)) + f"\n\n{PAST_Q_MSG_post}"+ "\n\nOnly output the query itself, nothing else.\nUser Query:"
                else:
                    follow_q_added_question = follow_q + "\n\nOnly output the query itself, nothing else.\nUser Query:"

                follow_query = ""
                while not follow_query:
                    response = chat_my(messages, follow_q_added_question, max_tokens=1024, model=model_ckpt)[-1]["content"]
                    follow_query = response.strip()
                
                messages = messages + [
                    {"role": "user", "content": follow_q},
                    {"role": "assistant", "content": follow_query}
                ]

                print(f"💬 Follow Query: {follow_query}")
                explored_queries.append(follow_query)
                item_follow = {"query": follow_query, "chains": []}

                # === ReAct for follow-up ===
                prompt_follow_a = template_a_follow.format(query=follow_query)
                messages = chat_my(messages, prompt_follow_a, stop="Observation:", max_tokens=1024, model=model_ckpt)
                temp = messages[-1]["content"]
                parsed = parse_response(temp, [api_name], api_info, proc_thought=True)

                for turn in range(max_turn):
                    if not parsed["parse_successful"]:
                        obs = parsed["parse_error_msg"]
                    elif parsed["finish"]:
                        item_follow["chains"].append({
                            "step": turn,
                            "parsed": parsed,
                            "observation": "Final Answer"
                        })
                        break
                    else:
                        try:
                            args = safe_json_loads(parsed["action_input"])
                            obs = run_tool(api_name, args)
                        except Exception as e:
                            obs = f"Error: {e}"

                    item_follow["chains"].append({
                        "step": turn,
                        "parsed": parsed,
                        "observation": obs
                    })
                    print(f"🔁 Follow Turn {turn}: {parsed.get('action')} → {obs[:120]}")

                    messages = chat_my(messages, "Observation: " + obs, stop="Observation:", max_tokens=1024, model=model_ckpt)
                    temp = messages[-1]["content"]
                    parsed = parse_response(temp, [api_name], api_info, proc_thought=True)

                # === Reflection for follow-up ===
                prompt_reflection_f = "Do you think you successfully fulfilled this query in the end? Respond with \"Yes\" or \"No\"."
                messages = chat_my(messages, prompt_reflection_f, stop="Observation:", max_tokens=1024, model=model_ckpt)
                res = messages[-1]["content"]
                successful = "Yes" if "Yes" in res else "No"
                print(f"✅ Follow-up Reflection: {successful}")

                item_follow["reflection"] = successful
                success_labels.append(successful)
                api_sessions.append(item_follow)

            # === Update dict and incrementally write ===
            data_dict[api_name] = api_sessions
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data_dict, f, indent=2, ensure_ascii=False)
            print(f"💾 Saved progress for '{api_name}' to {out_path}")

    print(f"\n🎉 All exploring done! Final results saved to {out_path}")

if __name__ == "__main__":
    main(
        resume_path=r"C:\Users\User\OneDrive\Desktop\temp\LLMs_in_the_Imaginarium\results\ste\merged_final_35_APIs.json"
    )
