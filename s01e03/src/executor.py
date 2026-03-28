import json
import time

from src.api import chat, extract_text, extract_tool_calls


MAX_TOOL_ROUNDS = 30


def log_query(query: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"Query: {query}")
    print("=" * 60)


def log_result(text: str) -> None:
    print(f"\nA: {text}")


def execute_tool_calls(tool_calls, handlers):
    print(f"\nTool calls: {len(tool_calls)}")
    results = []

    for call in tool_calls:
        args = json.loads(call["arguments"])
        print(f"  -> {call['name']}({json.dumps(args)})")

        try:
            handler = handlers[call["name"]]
            result = handler(args)
            print("    Success")
            results.append(
                {
                    "type": "function_call_output",
                    "call_id": call["call_id"],
                    "output": json.dumps(result),
                }
            )
        except Exception as error:  # noqa: BLE001
            print(f"    Error: {error}")
            results.append(
                {
                    "type": "function_call_output",
                    "call_id": call["call_id"],
                    "output": json.dumps({"error": str(error)}),
                }
            )

    return results


def process_query(query, config):
    chat_config = {
        "model": config["model"],
        "tools": config["tools"],
        "instructions": config["instructions"],
    }
    log_query(query)
    conversation = [{"role": "user", "content": query}]

    for _ in range(MAX_TOOL_ROUNDS):
        time.sleep(1)
        response = chat(**chat_config, input=conversation)
        tool_calls = extract_tool_calls(response)

        if not tool_calls:
            text = extract_text(response) or "No response"
            log_result(text)
            return text

        tool_results = execute_tool_calls(tool_calls, config["handlers"])
        conversation = [*conversation, *tool_calls, *tool_results]

    log_result("Max tool rounds reached")
    return "Max tool rounds reached"

