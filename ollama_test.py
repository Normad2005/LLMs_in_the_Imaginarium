from Exploration.my_llm import call_ollama

def main():
    model = "llama3.1:8b-instruct-fp16"  # 實驗室的可用模型
    prompt = "Hello"

    try:
        reply = call_ollama(model, prompt)
        print("=== 模型回應 ===")
        print(reply)
    except Exception as e:
        print("❌ 發生錯誤：", e)

if __name__ == "__main__":
    main()
