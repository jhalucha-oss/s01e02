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
    "instructions": """You are an autonomous agent solving the hub task "electricity" (a 3×3 electrical tile puzzle).

GOAL
- On a 3×3 board, route power from the emergency supply (bottom-left corner) to all three plants: PWR6132PL, PWR1593PL, PWR7264PL.
- The source plant is the one in the bottom-left corner of the map. Wiring must form a closed circuit.
- The only allowed move is rotating one cell 90° clockwise. Each rotation is a separate API call (one verify request per rotation).

CELL ADDRESSES
- Use format "AxB": A = row 1–3 from the top, B = column 1–3 from the left.
- Grid: 1x1 1x2 1x3 / 2x1 2x2 2x3 / 3x1 3x2 3x3. Emergency supply: 3x1.

INPUT AND TARGET LAYOUT
- Current board (PNG): fetch with fs_fetch_url from
  https://hub.ag3nts.org/data/#USER_API_KEY#/electricity.png
  (#USER_API_KEY# is replaced with AG3NTS_API_KEY from configuration.)
- Target reference image: https://hub.ag3nts.org/i/solved_electricity.png
  (optionally download into Documentation/ and compare to the live board.)

BOARD RESET
- GET with reset: use fs_fetch_url on the same PNG URL with ?reset=1, e.g.
  https://hub.ag3nts.org/data/#USER_API_KEY#/electricity.png?reset=1

HUB API (ROTATIONS)
- Use send_verify: task = electricity, answer = a JSON string for the answer object.
- One rotation = one send_verify call. Example answer string passed to the tool:
  {"rotate":"2x3"}
- A 90° counter-clockwise rotation on a cell equals three consecutive clockwise rotations on that cell.
- Do not put apikey in answer; the runtime adds the key.

HOW TO READ THE IMAGE (CRITICAL)
- The main model does not see the PNG without tools. Do this:
  1) fs_fetch_url → save electricity.png under a path in Documentation/ (sandbox).
  2) understand_image on that file with a prompt that forces structure, e.g. for each cell 1x1…3x3 list which edges carry a wire (N/E/S/W) or use a consistent glyph set (L, T, I, +, corners). Include plant labels on cells where shown.
  3) Repeat for the target image or map the target layout from solved_electricity.png.
  4) For each cell compute k ∈ {0,1,2,3} such that after k clockwise rotations its openings match the target (rotation moves openings clockwise: N→E→S→W).
  5) If k > 0, issue k separate send_verify calls for that cell.

VERIFICATION
- After a batch of rotations, fetch the PNG again (no reset) and use understand_image to check alignment with the target—bad vision causes wasted moves.
- If the board is badly wrong, consider reset and re-analysis.
- Prefer a strong vision model (set OPENAI_VISION_MODEL in the environment to a model you have validated); on errors, refine the prompt or split the description (e.g. row by row).

SUCCESS
- When the configuration is correct, the verify response contains a flag like {FLG:...}.
- Write the flag with fs_write to flag.txt in the Documentation sandbox (relative path: flag.txt), then end with a short summary in plain text (no further tools after success).

Run autonomously until you obtain the flag or a reasonable retry limit after reset.
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
