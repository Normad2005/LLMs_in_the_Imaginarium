from Exploration.my_llm import call_ollama

# llama3.1:8b-instruct-fp16
# gpt-oss

def main():
    model = "gpt-oss"
    prompt = "Hello"

    try:
        reply = call_ollama(model, prompt)
        print("=== 模型回應 ===")
        print(reply)
    except Exception as e:
        print("❌ 發生錯誤：", e)

if __name__ == "__main__":
    main()
