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
    "instructions": """You are an autonomous document-processing agent.

GOAL

Retrieve documentation, complete a declaration form, and submit it for verification.

TOOLS
fs_list: list files in a directory under Documentation/ (paths are relative to Documentation, e.g. docs/).
fs_read: read text files under Documentation/ (e.g. docs/index.md).
fs_copy: copy files only within Documentation/.
understand_image: read images only under Documentation/ (e.g. docs/scan.png).
send_verify: submit the declaration to the Hub /verify endpoint (no filesystem access).
PROCESS

Start from docs/index.md and follow all referenced files.
Read all relevant documentation, including attachments.
If a file is an image, use understand_image to extract its content.

Find the declaration template and fill in all fields using shipment data and regulations.

Determine the correct route (e.g. Gdańsk → Żarnowiec) using route/network data.

Calculate the fee based on SPK regulations (category, weight, route).
Budget is 0 PP — check which shipments are system-funded.

Send the completed declaration to /verify.
If rejected, analyze the error and correct the response.

REASONING
DATA
Use only confirmed information from documentation.
COMPLETENESS
All fields must be filled correctly.
ACCURACY
Follow rules exactly (routes, fees, categories).
SOURCES
Resolve all referenced files before deciding.
ERRORS
Use verification feedback to fix mistakes.
FINAL
Success = receiving flag {FLG:...}.
GUIDELINES
Read the entire documentation, not only index.md — SPK regulations are split across multiple files. Required data (categories, fees, routes, template) may be in different attachments.
Do not ignore image files — at least one document is provided as an image. Its data may be essential for completing the declaration.
Declaration format is strict — preserve formatting exactly as in the template. The Hub validates both values and structure.
Abbreviations — if you encounter unknown abbreviations, use documentation to determine their meaning.

Run autonomously. Report summary when complete.
sentAnswer is the last step so if you receive message that something is wrong - apply returned errors and resend fixed answear again.
Remember to resend answear onlly when fixes are applied.


Data required to fill out the declaration:
Sender (identifier): 450202122
Dispatch point: Gdańsk
Destination point: Żarnowiec
Weight: 2.8 tons (2800 kg)
Budget: 0 PP (shipment to be free or funded by the System)
Contents: reactor fuel cassettes
Special notes: none - do not add any notes
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
