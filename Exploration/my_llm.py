import json
import requests

def call_ollama(model: str, prompt: str, temperature: float = 0.7):
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

def chat_my(messages, new_message, visualize=True, model="llama3"):
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
