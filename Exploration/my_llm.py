import json
import requests
import time
import copy

LAB_KEY = "zhuantisheng"

def call_ollama(model: str, prompt: str, temperature: float = 0.7, max_tokens: int = None, stop: str = None,
                host: str = "lab", max_retries: int = 100, retry_delay: float = 3.0, return_tokens: bool = False):
    """
    若 return_tokens 為 True，回傳 (output_text, prompt_token_count)
    prompt_token_count 來自 Ollama 最後一個 done chunk 的 prompt_eval_count。
    否則僅回傳 output_text。
    """
    if host == "local":
        url = "http://localhost:11434/api/generate"
        options = {"temperature": temperature, "num_ctx": 16384}
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if stop is not None:
            options["stop"] = [stop]
        payload = {"model": model, "prompt": prompt, "options": options}
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
        if return_tokens:
            return output.strip(), prompt_tokens
        return output.strip()

    else:
        # === 雲端 API ===
        url = "https://ollama.nlpnchu.org/api/generate"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LAB_KEY}"
        }
        options = {"temperature": temperature, "num_ctx": 16384}
        if max_tokens is not None:
            options["num_predict"] = max_tokens
        if stop is not None:
            options["stop"] = [stop]
        payload = {"model": model, "prompt": prompt, "options": options}

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
                    if return_tokens:
                        return output.strip(), prompt_tokens
                    return output.strip()

            except requests.exceptions.RequestException as e:
                print(f"[warn] Network error on attempt {attempt}/{max_retries}: {e}")

            if attempt < max_retries:
                time.sleep(retry_delay)

        if return_tokens:
            return "Ollama cloud API failed after multiple retries. Possible server timeout or network issue.", -1
        return "Ollama cloud API failed after multiple retries. Possible server timeout or network issue."


def chat_my(messages, new_message, visualize=True, model="llama3.1:8b-instruct-fp16", max_tokens=None, stop=None, return_tokens: bool = False):
    """
    若 return_tokens 為 True，回傳 (messages, prompt_tokens)
    否則僅回傳 messages。
    """
    messages = copy.deepcopy(messages)
    messages.append({"role": "user", "content": new_message})
    
    if return_tokens:
        resp, prompt_tokens = get_chat_completion_my(model, messages, max_tokens=max_tokens, stop=stop, return_tokens=True)
        messages.append({"role": "assistant", "content": resp})
        if visualize:
            visualize_messages(messages[-2:])
        return messages, prompt_tokens
    else:
        resp = get_chat_completion_my(model, messages, max_tokens=max_tokens, stop=stop, return_tokens=False)
        messages.append({"role": "assistant", "content": resp})
        if visualize:
            visualize_messages(messages[-2:])
        return messages

def visualize_messages(messages):
    for m in messages:
        role = m["role"]
        print(f"{role.upper()}: {m['content']}\n")

def get_chat_completion_my(model, messages, max_tokens=None, stop=None, return_tokens: bool = False):
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

    if return_tokens:
        text, prompt_tokens = call_ollama(model, prompt, max_tokens=max_tokens, stop=stop, return_tokens=True)
        return text, prompt_tokens
    else:
        text = call_ollama(model, prompt, max_tokens=max_tokens, stop=stop, return_tokens=False)
        return text