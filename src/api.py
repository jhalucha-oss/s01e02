import json
from urllib import error, request

from src.config import api


def chat(*, model, input, tools=None, tool_choice="auto", instructions=None):
    if not api["api_key"]:
        raise RuntimeError("Missing AI_API_KEY environment variable")

    body = {"model": model, "input": input}

    if tools:
        body["tools"] = tools
        body["tool_choice"] = tool_choice

    if instructions:
        body["instructions"] = instructions

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
        raw_body = http_error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError:
            parsed = {"error": {"message": raw_body or str(http_error)}}

        message = parsed.get("error", {}).get(
            "message", f"Request failed with status {http_error.code}"
        )
        raise RuntimeError(message) from http_error
    except error.URLError as url_error:
        raise RuntimeError(f"Request failed: {url_error.reason}") from url_error

    if status >= 400 or data.get("error"):
        message = data.get("error", {}).get(
            "message", f"Request failed with status {status}"
        )
        raise RuntimeError(message)

    return data


def extract_tool_calls(response):
    return [item for item in response.get("output", []) if item.get("type") == "function_call"]


def extract_text(response):
    output_text = response.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    for item in response.get("output", []):
        if item.get("type") != "message":
            continue

        for content_item in item.get("content", []):
            text = content_item.get("text")
            if isinstance(text, str) and text:
                return text

    return None
