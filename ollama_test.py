from Exploration.my_llm import call_ollama
"""
- PetrosStav/gemma3-tools:27b
- gemma3:270M
- smollm2:135m
- qwq:latest
- qwen3:8b
- qwen3:32b
- qwen3:4b
- qwen3:30b
- qwen3:14b
- qwen3:1.7b
- phi4:latest
- nomic-embed-text:latest
- mistral:7b
- mistral-small:latest
- markliou/breeze-7b:instruct-64k
- magistral:latest
- llama3.3:latest
- llama3.2:latest
- llama3.1:latest
- llama3.1:8b-instruct-fp16
- jcai/llama3-taide-lx-8b-chat-alpha1:f16
- hf.co/voidful/Llama-3.1-TAIDE-R1-8B-Chat:latest
- gpt-oss:20b
- gpt-oss:120b
- gemma3:4b
- gemma3:27b
- gemma3:1b
- gemma3:12b
- deepseek-r1:8b
- deepseek-r1:32b
- deepseek-r1:1.5b
- cwchang/llama3-taide-lx-8b-chat-alpha1:latest
- bge-m3:latest
- bge-large:latest
"""
def main():
    model = "gpt-oss:120b"
    prompt = "Hello"

    try:
        reply = call_ollama(model, prompt)
        print("=== 模型回應 ===")
        print(reply)
    except Exception as e:
        print("❌ 發生錯誤：", e)

if __name__ == "__main__":
    main()
