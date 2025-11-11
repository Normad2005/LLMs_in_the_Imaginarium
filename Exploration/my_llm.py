import json
import requests
import time

LAB_KEY = "zhuantisheng"

def call_ollama(model: str, prompt: str, temperature: float = 0.7,
                host: str = "lab", max_retries: int = 3, retry_delay: float = 3.0):
    
    if host == "local":
        url = "http://localhost:11434/api/generate"
        payload = {"model": model, "prompt": prompt, "options": {"temperature": temperature}}
        resp = requests.post(url, json=payload, stream=True)
        output = ""
        for line in resp.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "response" in data:
                    output += data["response"]
        return output.strip()
    else:
        # 雲端 API
        url = "https://ollama.nlpnchu.org/api/generate"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LAB_KEY}"
        }
        payload = {"model": model, "prompt": prompt}
        resp = requests.post(url, json=payload, headers=headers)
        output = ""

        for attempt in range(1, max_retries + 1):
            resp = requests.post(url, json=payload, headers=headers)
            output = ""
            html_detected = False

            for line in resp.iter_lines():
                if not line:
                    continue
                text = line.decode("utf-8").strip()

                # 如果回傳 HTML，標記並中斷
                if text.startswith("<!DOCTYPE html>") or text.startswith("<html"):
                    html_detected = True
                    print(f"[warn] Received HTML response, will retry after {retry_delay}s.")
                    break

                try:
                    data = json.loads(text)
                    if "response" in data:
                        output += data["response"]
                except json.JSONDecodeError:
                    # 忽略非 JSON 格式行
                    continue

            if not html_detected:
                return output.strip()

            # 若偵測到 HTML 或輸出為空，則延遲重試
            if attempt < max_retries:
                time.sleep(retry_delay)

        return "Ollama cloud API returned an HTML error page. Likely a server timeout or service issue."


def chat_my(messages, new_message, visualize=True, model="llama3.1:8b-instruct-fp16"):
    messages.append({"role": "user", "content": new_message})
    resp = get_chat_completion_my(model, messages)
    messages.append({"role": "assistant", "content": resp})
    if visualize:
        visualize_messages(messages[-2:])
    return messages

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

    return call_ollama(model, prompt)
