"""Agent loop: chat → tool calls → results until completion."""

import json

from src.api import chat, extract_text, extract_tool_calls
from src.config import api
from src.helpers import logger as log
from src.native.tools import execute_native_tool, native_tools

MAX_STEPS = 100


def _run_tool(tool_call: dict) -> dict:
    args = json.loads(tool_call["arguments"])
    log.tool(tool_call["name"], args)
    try:
        result = execute_native_tool(tool_call["name"], args)
        output = json.dumps(result, ensure_ascii=False)
        err = result.get("error") if isinstance(result, dict) else None
        log.tool_result(tool_call["name"], err is None, output)
        return {"type": "function_call_output", "call_id": tool_call["call_id"], "output": output}
    except Exception as e:  # noqa: BLE001
        output = json.dumps({"error": str(e)}, ensure_ascii=False)
        log.tool_result(tool_call["name"], False, str(e))
        return {"type": "function_call_output", "call_id": tool_call["call_id"], "output": output}


def run(query: str) -> dict[str, str]:
    messages: list = [{"role": "user", "content": query}]
    tools = native_tools

    log.query(query)

    for step in range(1, MAX_STEPS + 1):
        log.api_step(f"Step {step}", len(messages))
        response = chat(
            input_messages=messages,
            tools=tools,
            instructions=api["instructions"],
        )
        log.api_done(response.get("usage"))

        tool_calls = extract_tool_calls(response)
        if not tool_calls:
            text = extract_text(response) or "No response"
            return {"response": text}

        messages.extend(response.get("output", []))
        for tc in tool_calls:
            messages.append(_run_tool(tc))

    raise RuntimeError(f"Max steps ({MAX_STEPS}) reached")
