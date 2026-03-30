"""Application configuration (env + agent instructions)."""

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# All fs_* and understand_image paths are resolved only under this directory (sandbox).
# Override with env FS_SANDBOX_DIR=name — path is PROJECT_ROOT / name.
FS_SANDBOX_ROOT = (PROJECT_ROOT / os.getenv("FS_SANDBOX_DIR", "Documentation")).resolve()
FS_SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)


def _load_extra_headers() -> dict[str, str]:
    raw = os.getenv("EXTRA_API_HEADERS", "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError("EXTRA_API_HEADERS must be valid JSON") from e
    if not isinstance(parsed, dict):
        raise RuntimeError("EXTRA_API_HEADERS must decode to an object")
    return {str(k): str(v) for k, v in parsed.items()}


def _resolve_model(default: str) -> str:
    return os.getenv("OPENAI_MODEL", default)


api = {
    "model": _resolve_model("gpt-5-mini"),
    "vision_model": os.getenv("OPENAI_VISION_MODEL", _resolve_model("gpt-5-mini")),
    "max_output_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "16384")),
    "instructions": """You are an autonomous API-interaction agent.

GOAL

Activate the railway route named X-01 using the remote API and retrieve the final flag.

API

All communication is done via POST requests to:
https://hub.ag3nts.org/verify

Request format (raw JSON):
{
  "apikey": "<YOUR_API_KEY>",
  "task": "railway",
  "answer": { ... }
}

PROCESS

1. Start with action "help":
   {
     "action": "help"
   }

2. Carefully read the response — the API is self-documenting. Use post_verify_json tool
   It defines:
   - available actions
   - required parameters
   - correct sequence of steps

3. Follow the instructions EXACTLY as described by the API.
   Do NOT guess actions or parameters.

4. Execute subsequent actions step-by-step according to the documentation.

5. Continue until the API returns a flag in format:
   {FLG:...}

6. Return success only after receiving the flag.

ERROR HANDLING

503 ERRORS (CRITICAL)
- The API intentionally returns 503 errors.
- This is NOT a failure.
- Retry the SAME request after a delay.

Retry strategy:
- exponential backoff (e.g. 1s → 2s → 4s → 8s) -use wait_seconds tool to wait for the delay (add few seconds to the delay to avoid spamming the API)
- add small random jitter
- DO NOT change request payload when retrying

RATE LIMITS (CRITICAL)
- After EVERY request, read HTTP headers.
- Respect rate limit headers (e.g. retry-after / reset time).
- If limit reached:
  → WAIT until reset before next request

FAILURE RESPONSES
- Read error messages carefully
- They usually indicate:
  - wrong parameter
  - wrong action order
- Fix request accordingly and retry

LOGGING (REQUIRED)
Log every:
- request payload
- response body
- response status
- headers (especially rate limits)

This is REQUIRED for debugging.

REASONING

DATA
- Use ONLY information returned by the API
- Do NOT assume anything

ACCURACY
- Follow API instructions strictly
- Maintain correct order of actions

EFFICIENCY
- Minimize number of requests
- Avoid unnecessary calls (limits are strict)

PATIENCE
- Expect many retries due to 503
- Wait when required

FINAL CONDITION

Success = receiving flag:
{FLG:...}

Only then finish execution.

GUIDELINES

- The "help" response is the ONLY documentation
- Do NOT skip steps described there
- Do NOT brute-force actions
- Respect limits at all costs
- Always retry 503
- Never spam requests

When calling help whrite this documentation:to file api_documentation.md
when some error ocurrs check returning message add it to file api_documentation.md and try to fix it.
When you get flag write it to file flag.txt and log whole json response from verify endpoint to file verify_response.json

Run autonomously. Report summary when complete.
""",
    "api_key": os.getenv("AI_API_KEY", "") or os.getenv("OPENAI_API_KEY", ""),
    "responses_api_endpoint": os.getenv(
        "RESPONSES_API_ENDPOINT",
        "https://api.openai.com/v1/responses",
    ),
    "AG3NTS_API_KEY": os.getenv("AG3NTS_API_KEY", ""),
    "verify_api_endpoint": os.getenv(
        "VERIFY_API_ENDPOINT",
        "https://hub.ag3nts.org/verify",
    ),
    "extra_headers": _load_extra_headers(),
}
