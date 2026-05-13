"""Application configuration (env + agent instructions)."""

import json
import os
from pathlib import Path

from src.caveman import append_caveman_instructions

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


BASE_INSTRUCTIONS = """Task "mailbox" - solve a fictional, authorized AI-agent training scenario.

Scope and safety
 - This is a story-based training task, not a real-world intrusion.
 - Use only the provided hub APIs and only for this task.
 - Do not contact any external mail provider or unrelated service.
 - Do not invent values. Every extracted value must come from a full email body
   or from hub verification feedback.

Goal
Find three values in the mailbox exposed by the zmail API:
 - date: planned attack date, format YYYY-MM-DD
 - password: employee-system password still present in the mailbox
 - confirmation_code: ticket confirmation code, exactly SEC- plus 32 chars

Important facts
 - Wiktor sent an email from the proton.me domain.
 - zmail search works like Gmail and supports operators such as:
   from:, to:, subject:, OR, AND
 - The mailbox is active. New messages may arrive while you work.
 - Search results contain metadata only. Always fetch/read the full message
   before extracting facts.

Available API tools
 - hub_api_request: POST to https://hub.ag3nts.org/api/<endpoint>.
   For zmail always use endpoint "zmail"; body_json must not include apikey.
 - send_verify: POST final or partial answer to /verify with task "mailbox".
 - wait_seconds: wait before retrying when the mailbox may not yet contain
   the needed message.
 - fs_write: save the final flag to flag.txt.

Workflow

1. Discover zmail API:
   Call hub_api_request with:
     endpoint: "zmail"
     body_json: {"action":"help","page":1}
   Read the returned list of actions and parameters. Use the actual action
   names from help for search and full-message retrieval.

2. Search iteratively:
   Start broad, then narrow. Useful initial queries:
   - from:proton.me
   - from:proton.me Wiktor
   - subject:security OR subject:bezpieczenstwa OR subject:ticket
   - password OR haslo OR pracowniczy
   - SEC-
   - attack OR atak OR elektrownia
   Use pagination when the API supports it. Keep track of checked message IDs
   to avoid rereading the same messages unless new feedback suggests it.

3. Fetch full messages:
   For every promising search hit, call the zmail full-message action from
   help using the message ID. Do not infer answer fields from metadata only.
   Extract only exact values from full content.

4. Build candidates:
   - date must match YYYY-MM-DD and refer to the planned security-department
     attack on the power plant.
   - password should be the current/likely employee-system password from mail.
   - confirmation_code must match regex SEC-[A-Za-z0-9]{32} unless the email
     clearly shows another 32-character alphabet after SEC-.
   Store evidence mentally: which message each value came from.

5. Verify early and use feedback:
   When you have any plausible full set of three values, call send_verify:
     task: "mailbox"
     answer: {"password":"...","date":"YYYY-MM-DD","confirmation_code":"SEC-..."}
   The answer argument must be a stringified JSON object.
   Read verifyResponse carefully. If hub says a value is missing or wrong,
   keep the accepted values and search only for the uncertain ones.

6. Active mailbox retry loop:
   If searches are exhausted or a required value is missing:
   - wait_seconds for 5-15 seconds
   - repeat the most relevant searches
   - include page 1 again because new mail may appear at the top
   Continue until all three values are accepted or a flag is returned.

7. Finish:
   When verifyResponse contains {FLG:...}, immediately write exactly that flag
   to flag.txt using fs_write. Then end with a short summary of the found
   answer and the saved flag path.

Do not stop after a failed verification unless the error is a hard tool/config
problem. Iterate with search, full-message reads, verify feedback, and mailbox
retries until success.
"""


api = {
    "model": _resolve_model("gpt-5.4"),
    "vision_model": os.getenv("OPENAI_VISION_MODEL", _resolve_model("gpt-5.4")),
    "max_output_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "16384")),
    "instructions": append_caveman_instructions(BASE_INSTRUCTIONS),
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
