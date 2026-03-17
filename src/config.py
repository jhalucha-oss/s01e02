import json
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SANDBOX_ROOT = PROJECT_ROOT / "sandbox"


def _load_extra_headers() -> dict[str, str]:
    raw = os.getenv("EXTRA_API_HEADERS", "").strip()
    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError("EXTRA_API_HEADERS must be valid JSON") from error

    if not isinstance(parsed, dict):
        raise RuntimeError("EXTRA_API_HEADERS must decode to an object")

    return {str(key): str(value) for key, value in parsed.items()}


sandbox = {
    "root": SANDBOX_ROOT,
}

sandbox["root"].mkdir(parents=True, exist_ok=True)

api = {
    "model": os.getenv("OPENAI_MODEL", "gpt-4.1"),
    "instructions": (
        "You are a helpful assistant with access to a sandboxed filesystem.\n"
        "You can list, read, write, and delete files within the sandbox.\n"
        "Always use the available tools to interact with files.\n"
        "Be concise in your responses."
    ),
    "api_key": os.getenv("AI_API_KEY", ""),
    "responses_api_endpoint": os.getenv(
        "RESPONSES_API_ENDPOINT",
        "https://api.openai.com/v1/responses",
    ),
    "extra_headers": _load_extra_headers(),
}
