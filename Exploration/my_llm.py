import json
import requests
import time

LAB_KEY = "zhuantisheng"

def call_ollama(model: str, prompt: str, temperature: float = 0.7,
                host: str = "lab", max_retries: int = 100, retry_delay: float = 3.0):
    """
    回傳 (output_text, prompt_token_count)
    prompt_token_count 來自 Ollama 最後一個 done chunk 的 prompt_eval_count。
    若無法取得則回傳 -1。
    """
    if host == "local":
        url = "http://localhost:11434/api/generate"
        payload = {"model": model, "prompt": prompt, "options": {"temperature": temperature}}
        resp = requests.post(url, json=payload, stream=True)
        output = ""
        prompt_tokens = -1
        for line in resp.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    output += data["response"]
                if data.get("done", False):
                    prompt_tokens = data.get("prompt_eval_count", -1)
        return output.strip(), prompt_tokens

    else:
        # === 雲端 API ===
        url = "https://ollama.nlpnchu.org/api/generate"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LAB_KEY}"
        }
        payload = {"model": model, "prompt": prompt}

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.post(url, json=payload, headers=headers, stream=True, timeout=120)
                output = ""
                prompt_tokens = -1
                html_detected = False

                for line in resp.iter_lines():
                    if not line:
                        continue
                    text = line.decode("utf-8").strip()

                    if text.startswith("<!DOCTYPE html>") or text.startswith("<html"):
                        html_detected = True
                        print(f"[warn] Received HTML response on attempt {attempt}/{max_retries}, retrying after {retry_delay}s...")
                        break

                    try:
                        data = json.loads(text)
                        if "response" in data:
                            output += data["response"]
                        # done chunk 帶有 token 統計
                        if data.get("done", False):
                            prompt_tokens = data.get("prompt_eval_count", -1)
                    except json.JSONDecodeError:
                        continue

                if not html_detected:
                    return output.strip(), prompt_tokens

            except requests.exceptions.RequestException as e:
                print(f"[warn] Network error on attempt {attempt}/{max_retries}: {e}")

            if attempt < max_retries:
                time.sleep(retry_delay)

        return "Ollama cloud API failed after multiple retries. Possible server timeout or network issue.", -1


def chat_my(messages, new_message, visualize=True, model="llama3.1:8b-instruct-fp16"):
    """
    回傳 (messages, prompt_tokens)
    prompt_tokens 是這次呼叫的 prompt token 數，-1 代表無法取得。
    """
    messages.append({"role": "user", "content": new_message})
    resp, prompt_tokens = get_chat_completion_my(model, messages)
    messages.append({"role": "assistant", "content": resp})
    if visualize:
        visualize_messages(messages[-2:])
    return messages, prompt_tokens

def visualize_messages(messages):
    for m in messages:
        role = m["role"]
        print(f"{role.upper()}: {m['content']}\n")

def get_chat_completion_my(model, messages):
    prompt = ""
    for m in messages:
        role = m["role"]
        content = m["content"]
        if role == "system":
            prompt += f"System: {content}\n"
        elif role == "user":
            prompt += f"User: {content}\n"
        elif role == "assistant":
            prompt += f"Assistant: {content}\n"
    prompt += "\nAssistant:"

    text, prompt_tokens = call_ollama(model, prompt)
    return text, prompt_tokens