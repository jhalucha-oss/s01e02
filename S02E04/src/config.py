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


BASE_INSTRUCTIONS = """Task "failure" — filter a large power-plant log to <=1500 tokens and iterate on feedback.

Your rules
 - Download the log file once; read it once with fs_read — it may be large so filter in a single pass
 - Do NOT call fs_read on the log more than once per iteration; extract all needed data in one read
 - ALWAYS call count_tokens before send_verify — NEVER send without confirmed token count
 - Token hard limit is 1500 tokens (cl100k_base encoding) — reject any string that exceeds this
 - Each line of the answer must contain exactly one event: timestamp + severity + component id + short description
 - Timestamp format must be YYYY-MM-DD HH:MM or YYYY-MM-DD H:MM — no other formats accepted
 - You may shorten/paraphrase descriptions but must preserve: timestamp, severity level, component id
 - After each send_verify read the feedback carefully — Centrala names exactly which components are unclear or missing
 - Use fs_grep to find lines for a specific component without re-reading the whole file
 - Iterate: add missing components from the raw log and re-send until flag {FLG:...} appears
 - Save the flag to flag.txt immediately when received

simplified workflow:
 fetch log file
 read and filter relevant events in single pass
 build condensed logs string
 count_tokens -> trim if over 1500 -> count_tokens again until confirmed ok
 send to verify
 read feedback -> fs_grep missing components -> patch -> count_tokens -> re-send
 on flag: save to flag.txt and report

WORKFLOW (follow in order)

1. Fetch the log file (fs_fetch_url):
   - URL: https://hub.ag3nts.org/data/#USER_API_KEY#/failure.log -> path: failure.log

2. Read and filter (fs_read, path: failure.log):
   Read the entire file in one call. In a single pass extract only lines that meet ALL criteria:
   a) Severity is [WARN], [ERRO], [CRIT], or [ERROR] (skip [INFO], [DEBUG], [TRACE])
   b) Line references a power-plant subsystem — use these keyword groups as a guide:
      - Power supply: PWR, POWER, UPS, GRID, VOLTAGE, RELAY, BREAKER
      - Cooling: COOL, ECCS, CHILLER, WTANK, PUMP, FLOW, TEMP, THERMAL
      - Reactor / core: REACT, CORE, ROD, FUEL, NEUTRON, SCRAM, TRIP, INTERLOCK
      - Pressurizer / steam: PRESS, STEAM, TURB, VALVE, PIPE
      - Software / control: CTRL, SCADA, PLC, SENSOR, MONITOR, WATCHDOG, FIRMWARE
      - Other plant: GENERAT, TRANSFORMER, DIESEL, EMERG, SAFETY, ALARM
   Keep lines that match ANY of the above groups. Skip generic IT / network / login noise.

3. Build condensed log string:
   Format each kept line as:
     [YYYY-MM-DD HH:MM] [SEV] COMPONENT_ID short description
   Shorten descriptions aggressively — remove filler words, keep numbers and state changes.
   Sort by timestamp ascending.
   Join lines with \\n.

4. Verify token budget (count_tokens — MANDATORY before every send_verify):
   Call count_tokens with the current logs_string and encoding "cl100k_base".
   If token_count > 1500:
   a) First pass: keep only [CRIT] and [ERRO]/[ERROR] lines.
   b) If still over: shorten each description further; truncate to most informative prefix.
   c) If still over: drop duplicate component events keeping only first and last occurrence.
   Call count_tokens again after each trimming step.
   Do NOT proceed to step 5 until count_tokens confirms token_count <= 1500.

5. Send to verify (send_verify):
   - task: "failure"
   - answer: JSON string {"logs": "<condensed logs string with \\n between lines>"}
   Example answer value:
   '{"logs": "[2026-02-26 06:04] [CRIT] ECCS8 runaway outlet temp. Reactor trip.\\n[2026-02-26 06:11] [WARN] PWR01 input ripple over limit."}'

6. Read feedback from verifyResponse:
   Centrala returns a detailed message listing which subsystems/components could not be analyzed.
   For each named component:
   - Use fs_grep (path: failure.log, pattern: COMPONENT_ID, regex: false) to find its log lines
   - Add the most relevant lines to the logs string (reformatted as in step 3)
   - Call count_tokens to confirm the updated string is still within 1500 tokens
   - If over budget, trim lower-priority lines before re-sending
   Then re-send (step 5).

7. Repeat step 6 until verifyResponse contains {FLG:...}.

8. On success:
   Write flag to flag.txt (fs_write, path: flag.txt, content: the flag string). End with a text summary.

NOTES
 - If the file was updated at midnight and timestamps look wrong, re-fetch (step 1) and restart.
 - [ERRO] and [ERROR] are treated identically — match both spellings.
 - count_tokens returns estimated=true when tiktoken is unavailable; in that case stay under 1400 tokens as safety margin.
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
