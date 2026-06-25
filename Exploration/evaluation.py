from copy import deepcopy
from utils import find_reverse, random_choose, parse_response, strip_end
from my_llm import chat_my
import json
import re

string_match_APIs = [
  "verify_email",
  "get_car_makes",
  "get_divisions_near_location",
  "convert_currency",
  "calculate_mortgage_payment",
  "get_all_mvc2_characters",
  "get_filtered_game_giveaways",
  "get_lol_champion_stats",
  "get_soccer_tournaments",
  "get_f1_latest_news",
  "get_handball_scheduled_matches",
  "get_airlines",
  "get_motorcycle_data",
]

model_ckpts = "gpt-oss:120b"


with open("tool_metadata/tool_description.json", "r", encoding="utf-8") as f:
    TOOL_DESCRIPTION = json.load(f)

def format_action_input(raw_input):
    if not isinstance(raw_input, str):
        return json.dumps(raw_input, indent=2, ensure_ascii=False)

    clean_input = re.sub(r'//.*', '', raw_input).strip()

    try:
        parsed = json.loads(clean_input)
        if isinstance(parsed, (dict, list)):
            return json.dumps(parsed, indent=4, ensure_ascii=False)
        if isinstance(parsed, str) and parsed.strip().startswith("{"):
            inner = json.loads(parsed)
            return json.dumps(inner, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return raw_input

def eval_pred_file(file_name, key_output='model_output', is_parsed=True, visualize=False):

    with open(file_name, "r", encoding='utf-8') as f:
        dataset = json.load(f)

    for gt_api in dataset:

        examples = dataset[gt_api]
        for ii in range(len(examples)):
            item = examples[ii]
        
            item['no_call'] = 0
            if is_parsed:
                parsed = item['parsed_result']
            else:
                #暫時用不到
                res = item[key_output].strip()
                #parsed = parse_response(res, API_name_list=list(dataset.keys()), api_descriptions="XXX", proc_toolken=True, ground_API=True)
            
            if parsed['finish']:
                item['err'] = 0
                item['no_call'] = 1
                examples[ii] = item
                continue
            
            if not parsed['parse_successful']:
                item['err'] = 1
                examples[ii] = item
                continue

            try:
                json.loads(parsed['action_input'])
            except:
                item['err'] = 1
                examples[ii] = item
                continue
                
            item['err'] = 0
            
            if parsed['action'] != gt_api:
                item['api_match'] = 0
            else:
                item['api_match'] = 1
                
                gt_action_input = item['action_input']
                model_action_input = parsed['action_input']

                gt_dict = gt_action_input
                model_dict = json.loads(model_action_input)

                # check semantic correctenss based on API call
                if gt_api in string_match_APIs:
                    # check via string matching
                    string_same = True

                    for key, val in gt_dict.items():
                        if key in model_dict and str(model_dict[key]).strip().lower() == str(val).strip().lower():
                            pass
                        else:
                            string_same = False
                            break
                    item['args_correct'] = int(string_same)

                else:
                    # check the correctness via ChatGPT
                    messages = [
                        {"role": "system", "content": "You are a helpful assistant."}
                    ]

                    msg = "Your task is to judge whether an API call is correct with respect to the given ground truth API call.\n"\
                    "API Description:\n{}\n\n" \
                    "The ground truth API call is:\nAPI name: {}\nAPI arguments: {}\n\n" \
                    "The API call that you need to verify the correctness is:\nAPI name: {}\nAPI arguments: {}\n\n" \
                    "The API call doesn't have to be exactly identical to the ground truth, but:\n"\
                    "The argument names and structure should exactly follow the API Description.\n"\
                    "Now say your judgment. Your response should always start with \"Yes.\" or \"No.\" indicating whether it's correct.\nYour response:"

                    jud = chat_my(messages, msg.format(json.dumps(TOOL_DESCRIPTION[gt_api], indent=2, ensure_ascii=False), gt_api, json.dumps(gt_dict), gt_api, format_action_input(model_dict)), model=model_ckpts)[-1]['content']

                    item['args_correct'] = int("No." not in jud)
                    
            examples[ii] = item

        dataset[gt_api] = examples

    with open(file_name, "w", encoding='utf-8') as f:
        json.dump(dataset, f)
        
        
def eval_batch(file_name, key_list=None):
    if type(file_name) == str:
        with open(file_name, "r") as f:
            dataset_evaled = json.load(f)
    else:
        dataset_evaled = file_name
    
    correct = 0
    syntax_err, no_call = 0, 0
    total = 0
    api_match = 0
    non_err = 0
    total_prompt_chars = 0
    prompt_chars_count = 0
        
    for key, examples in dataset_evaled.items():
        if not (key_list is None or key in key_list):
            continue

        for item in examples:
            total += 1

            # 累計 prompt token 數（若有記錄且有效）
            pt = item.get("prompt_tokens", -1)
            if pt and pt > 0:
                total_prompt_chars += pt
                prompt_chars_count += 1
            
            if item['no_call']:
                no_call += 1
                continue
            
            if item['err']:
                syntax_err += 1
                continue
                
            non_err += 1
            
            if item['api_match']:
                api_match += 1
                correct += item['args_correct']
                continue
    
    print("wellformed:", round(100*(non_err/total), 3))
    print("api match:", round(100*api_match/non_err, 3) if non_err else "N/A")
    print("correct:", round(100*correct/total, 3))
    if prompt_chars_count:
        avg_tokens = total_prompt_chars / prompt_chars_count
        print(f"avg prompt tokens: {round(avg_tokens)}")

if __name__ == "__main__":
    eval_pred_file("results/icl/outputs_ICL_filtered.json")
    eval_batch("results/icl/outputs_ICL_filtered.json")