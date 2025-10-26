# === ste_runner.py ===
import sys, os
import re
import json
from datetime import datetime
from utils import parse_response, strip_end
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
def main(model_ckpt="llama3", num_episodes=3, num_stm_slots=2, max_turn=3, dir_write="results/ste/"):
    os.makedirs(dir_write, exist_ok=True)

    # === 載入 Prompt Template ===
    with open("prompts/prompt_explore.txt", "r", encoding="utf-8") as f:
        prompt_template = f.read().strip()

    parts = prompt_template.split("=========")
    template_q = parts[0].strip()
    template_a = parts[1].strip()
    template_q_follow = parts[2].strip()
    template_a_follow = parts[3].strip()

    past_msg_pre = "Below are queries you have already explored:"
    past_msg_post = "Try to explore new ones next."

    data_dict = {}

    # === 從 RapidAPI Registry 載入所有 API ===
    api_list = list(TOOL_REGISTRY.keys())

    # === 每次只探索一個 API ===
    for api_name in api_list:
        print(f"\n===== Exploring {api_name} =====")

        explored_queries, success_labels, all_sessions = [], [], []
        api_info = f"API_name: {api_name}\nDescription:\n{json.dumps(TOOL_DESCRIPTION[api_name], indent=2, ensure_ascii=False)}"

        for ep in range(num_episodes):
            print(f"\n=== Episode {ep} ===")
            messages = [{"role": "system", "content": "You are a helpful assistant."}]

            # === Step 1: Query 生成 ===
            prompt_q = template_q.format(api_descriptions=api_info)
            strip_end(prompt_q, "User Query:").strip()
            if explored_queries:
                prompt_q += f"\n\n{past_msg_pre}\n" + "\n".join(LTM(explored_queries, success_labels)) + f"\n\n{past_msg_post}"+ "\n\nUser Query:"

            response = call_ollama(model_ckpt, prompt_q)
            query = response.strip()
            print(f"🧠 New Query: {query}")
            explored_queries.append(query)
            item = {"query": query, "chains": []}

            # === Step 2: ReAct Chain ===
            prompt_a = template_a.format(api_descriptions=api_info,api_names=api_name, query=query)
            messages = chat_my(messages, prompt_a)
            temp = messages[-1]["content"]
            parsed = parse_response(temp, [api_name], api_info)

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

                messages = chat_my(messages, "Observation: " + obs)
                temp = messages[-1]["content"]
                parsed = parse_response(temp, [api_name], api_info)

            # === Step 3: Reflection ===
            chain_summary = json.dumps(item["chains"][-1], ensure_ascii=False, indent=2) #取最後一回合
            reflection_prompt = f"""
                User Query:
                {query}

                Reasoning chain:
                {chain_summary}

                Did you successfully fulfill this query? Reply exactly 'Yes' or 'No'.
                """
            reflection_prompt = textwrap.dedent(reflection_prompt)

            res = call_ollama(model_ckpt, reflection_prompt, temperature=0)
            successful = "Yes" if "Yes" in res else "No"
            print(f"✅ Reflection: {successful}")

            item["reflection"] = successful
            success_labels.append(successful)
            all_sessions.append(item)

            # === Step 4: Follow-up ===
            for f_idx in range(num_stm_slots - 1):
                print(f"\n--- Follow-up #{f_idx + 1} ---")

                follow_q = strip_end(template_q_follow, "User Query:").strip()
                if explored_queries:
                    follow_q += f"\n\n{past_msg_pre}\n" + "\n".join(LTM(explored_queries, success_labels)) + f"\n\n{past_msg_post}" + "\n\nUser Query:"

                response = chat_my(messages, follow_q)[-1]["content"]
                follow_query = response.strip()
                print(f"💬 Follow Query: {follow_query}")
                explored_queries.append(follow_query)
                item_follow = {"query": follow_query, "chains": []}

                # === ReAct for follow-up ===
                prompt_follow_a = template_a_follow.format(query=follow_query)
                messages = chat_my(messages, prompt_follow_a)
                temp = messages[-1]["content"]
                parsed = parse_response(temp, [api_name], api_info)

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

                    messages = chat_my(messages, "Observation: " + obs)
                    temp = messages[-1]["content"]
                    parsed = parse_response(temp, [api_name], api_info)

                # === Reflection for follow-up ===
                chain_summary = json.dumps(item_follow["chains"][-1], ensure_ascii=False, indent=2) #取最後一回合
                reflection_prompt = f"""
                    User Query:
                    {follow_query}

                    Reasoning chain:
                    {chain_summary}

                    Did you successfully fulfill this query? Reply exactly 'Yes' or 'No'.
                    """
                reflection_prompt = textwrap.dedent(reflection_prompt)

                res = call_ollama(model_ckpt, reflection_prompt, temperature=0)
                successful = "Yes" if "Yes" in res else "No"
                print(f"✅ Follow-up Reflection: {successful}")

                item_follow["reflection"] = successful
                success_labels.append(successful)
                all_sessions.append(item_follow)

        data_dict[api_name] = all_sessions

    # === 寫出結果 ===
    out_path = os.path.join(dir_write, f"data_{RUN_ID}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data_dict, f, indent=2, ensure_ascii=False)
    print(f"\n📁 Results saved to {out_path}")

if __name__ == "__main__":
    main()
