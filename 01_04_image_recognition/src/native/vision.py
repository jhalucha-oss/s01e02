import json
from urllib import error, request

from src.config import api
from src.helpers.response import extract_response_text
from src.helpers.stats import record_usage


def vision(*, image_base64: str, mime_type: str, question: str) -> str:
    if not api["api_key"]:
        raise RuntimeError("Set AI_API_KEY or OPENAI_API_KEY")

    body = {
        "model": api["vision_model"],
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": question},
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{image_base64}",
                    },
                ],
            }
        ],
    }

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
            parsed = {"error": {"message": raw}}
        msg = parsed.get("error", {}).get("message", str(http_error))
        raise RuntimeError(msg) from http_error
    except error.URLError as url_error:
        raise RuntimeError(f"Request failed: {url_error.reason}") from url_error

    if status >= 400 or data.get("error"):
        msg = data.get("error", {}).get("message", f"Vision failed ({status})")
        raise RuntimeError(msg)

    record_usage(data.get("usage"))
    return extract_response_text(data) or "No response"
