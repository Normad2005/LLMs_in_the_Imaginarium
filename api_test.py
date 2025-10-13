import json
from tool_runner import get_rapidapi_response
from config.api_keys import RAPIDAPI_KEY
from tool_registry import TOOL_REGISTRY


def run_tool(api_name: str, args: dict, truncate: int = 2048):
    """
    呼叫指定 API，只需提供 api_name 與 args 即可。
    例如：
      run_tool("get_fun_quote", {"topic": "fun"})
    """
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


if __name__ == "__main__":
    print("=== 🔧 Tool Test Interface ===")
    print("可用 API：")
    for name in TOOL_REGISTRY.keys():
        print(f" - {name}")
    print("==============================")

    api_name = input("請輸入要呼叫的 API 名稱: ").strip()
    param_json = input("請輸入參數 (JSON 格式，如 {\"topic\":\"fun\"}): ").strip()

    try:
        params = json.loads(param_json) if param_json else {}
    except json.JSONDecodeError:
        print("❌ JSON 格式錯誤，請檢查輸入")
        exit(1)

    print(f"\n🚀 正在呼叫 {api_name}({params})...\n")

    response = run_tool(api_name, params)
    print("\n📬 API 回傳結果：\n")
    print(response)
