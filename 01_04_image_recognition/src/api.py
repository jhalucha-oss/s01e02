import json
from urllib import error, request

from src.config import api
from src.helpers.response import extract_response_text
from src.helpers.stats import record_usage


def chat(
    *,
    model: str | None = None,
    input_messages: list,
    tools=None,
    tool_choice: str = "auto",
    instructions: str | None = None,
    max_output_tokens: int | None = None,
):
    if not api["api_key"]:
        raise RuntimeError("Set AI_API_KEY or OPENAI_API_KEY")

    body: dict = {
        "model": model or api["model"],
        "input": input_messages,
    }
    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice
    if instructions is not None:
        body["instructions"] = instructions
    mot = max_output_tokens if max_output_tokens is not None else api["max_output_tokens"]
    if mot:
        body["max_output_tokens"] = mot

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api['api_key']}",
        **api["extra_headers"],
    }
    payload = json.dumps(body).encode("utf-8")
    req = request.Request(
        api["responses_api_endpoint"],
        data=payload,
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            status = response.getcode()
    except error.HTTPError as http_error:
        raw = http_error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"error": {"message": raw or str(http_error)}}
        msg = parsed.get("error", {}).get("message", f"HTTP {http_error.code}")
        raise RuntimeError(msg) from http_error
    except error.URLError as url_error:
        raise RuntimeError(f"Request failed: {url_error.reason}") from url_error

    if status >= 400 or data.get("error"):
        msg = data.get("error", {}).get("message", f"Request failed with status {status}")
        raise RuntimeError(msg)

    record_usage(data.get("usage"))
    return data


def extract_tool_calls(response: dict) -> list:
    return [item for item in response.get("output", []) if item.get("type") == "function_call"]


def extract_text(response: dict) -> str | None:
    t = extract_response_text(response)
    return t if t else None
