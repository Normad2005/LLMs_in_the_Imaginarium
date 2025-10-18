# === postprocessing.py ===
import os
import json
import random
from copy import deepcopy
from my_llm import chat_my, call_ollama


def main(
    input_path: str = "results/ste/data_latest.json",
    filter_model_ckpt: str = "llama3",
    paraphrase_model_ckpt: str = "llama3",
    target_num_train_per_API: int = 150,
    num_para_train_max: int = 6,
    dir_write: str = "results/ste/",
    save_file_name: str = "tool_data_train.json",
):
    os.makedirs(dir_write, exist_ok=True)

    # === 讀入探索資料 ===
    with open(input_path, "r", encoding="utf-8") as f:
        data_dict = json.load(f)

    # === 載入 filter prompt ===
    with open("prompts/prompt_filtering.txt", "r", encoding="utf-8") as f:
        prompt_filtering_template = f.read().strip()

    dataset = {}
    print(f"🔍 Filtering data from {len(data_dict)} APIs")

    for api_name, sessions in data_dict.items():
        examples = []
        print(f"\n=== Processing {api_name} ===")

        for session in sessions:
            for item in session.get("chains", []):
                pass  # safeguard (older data formats)

            # 每個 session 可能有多個 item（episode slot）
            for item in session.get("chains", []):
                pass  # placeholder in case structure varies

        # 你的 ste_runner 結構是 all_sessions → item["chains"]
        for item in sessions:
            chains = item.get("chains", [])
            if not chains:
                continue

            last_step = chains[-1]["parsed"]
            if not last_step.get("finish", False):
                continue

            # 取得最後成功的 API 呼叫
            last_action = None
            for step in reversed(chains):
                if step["parsed"].get("parse_successful", False):
                    last_action = step["parsed"]
                    break
            if not last_action:
                continue

            # === 用 LLM 過濾 ===
            prompt_criticize = prompt_filtering_template.format(
                api_descriptions=last_action.get("api_descriptions", ""),
                query=item.get("query", ""),
                chains=json.dumps(chains, ensure_ascii=False, indent=2),
                final_ans=last_step.get("final_ans", ""),
            )

            judgment = call_ollama(filter_model_ckpt, prompt_criticize)
            item["judgment"] = judgment

            if "No" in judgment:
                continue

            # === 儲存合格範例 ===
            examples.append({
                "query": item["query"],
                "action": last_action.get("action", api_name),
                "action_input": last_action.get("action_input", {}),
                "observation": chains[-1]["observation"],
                "final_ans": last_step.get("final_ans", ""),
            })

        dataset[api_name] = examples
        print(f"✅ {api_name}: kept {len(examples)} examples")

    # === Paraphrase ===
    dataset_paraphrased = {}
    print("\n🌀 Starting paraphrasing...")

    for api_name, examples in dataset.items():
        if not examples:
            continue

        num_para = min(
            round(target_num_train_per_API / (len(examples) + 0.001)) - 1,
            num_para_train_max,
        )

        para_list = []
        for ex in examples:
            base_query = ex["query"]
            ex_list = [ex]

            # 第一次改寫
            para_prompt = f"""Below is a user query. Rephrase it in a different way but keep the meaning.
Original query:
{base_query}

Your paraphrase:"""
            paraphrased = call_ollama(paraphrase_model_ckpt, para_prompt).strip()
            ex_list.append({"query": paraphrased})

            # 其他改寫版本
            for _ in range(num_para - 1):
                follow_prompt = "Try paraphrasing it again in a new way (avoid being too similar):"
                new_para = call_ollama(paraphrase_model_ckpt, follow_prompt).strip()
                ex_list.append({"query": new_para})

            para_list.append(ex_list)
        dataset_paraphrased[api_name] = para_list

    # === 組成最終訓練集 ===
    tool_data_train = []
    for api_name, para_group in dataset_paraphrased.items():
        for ex_list in para_group:
            if not ex_list:
                continue
            seed = ex_list[0]
            tool_data_train.append(seed)
            for i in range(1, len(ex_list)):
                tmp = deepcopy(seed)
                tmp["query"] = ex_list[i]["query"]
                tool_data_train.append(tmp)

    random.shuffle(tool_data_train)
    out_path = os.path.join(dir_write, save_file_name)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(tool_data_train, f, indent=2, ensure_ascii=False)

    print(f"\n📦 Saved {len(tool_data_train)} examples to {out_path}")


if __name__ == "__main__":
    main()
