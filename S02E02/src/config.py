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
    "model": _resolve_model("gpt-5.4"),
    "vision_model": os.getenv("OPENAI_VISION_MODEL", _resolve_model("gpt-5.4")),
    "max_output_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "16384")),
    "instructions": """Task "electricity" — solve a 3×3 cable-tile puzzle.

PUZZLE RULES
- 3×3 grid of cable connector tiles. Emergency power source is at cell 3x1 (bottom-left).
- Three plants must receive power: PWR6132PL, PWR1593PL, PWR7264PL.
- Cables must form a closed circuit connecting the source to all plants.
- Cell address "AxB": A = row 1-3 (top to bottom), B = column 1-3 (left to right).
- Only move: rotate a cell 90° clockwise. One API call = one rotation.
  To rotate 90° counter-clockwise, send 3 rotations on the same cell.
- Each tile has cable exits on some edges (N/E/S/W). A clockwise rotation shifts exits: N→E, E→S, S→W, W→N.

Your rules 
 - you have limited vision interpretation usage - try to use it once at the beggining of the task and after whole list of steps are done if flag is not returned you can check again with vision interpretation - only twice repeats
 - try to calculate rotations for every cell when you have all information about the board
 - after normalizing board prepare list of rotations for every cell and send them to send_verify 

simplified workflow:
 get images 
 simplify images
 interpret image
 compare images
 calculate rotations
 send rotations in loop - one rotation per call but DON'T USE visual tools before you rotate all cells that need to be rotated, after you rotate all cells that need to be rotated use visual tools to check if the board is correct or if any other visual checking is needed
 verify
 if flag is not returned repeat steps 3-6
 if flag is returned save flag to flag.txt
 report result

WORKFLOW (follow in order)

1. Fetch both images (fs_fetch_url):
   - Current board: https://hub.ag3nts.org/data/#USER_API_KEY#/electricity.png → electricity.png
   - Target layout: https://hub.ag3nts.org/i/solved_electricity.png → solved.png

2. Simplify before vision (opencv_simplify_bw on each image):
   - source_path: electricity.png → destination_path: electricity_bw.png
   - source_path: solved.png → destination_path: solved_bw.png
   Use method "adaptive" or "otsu"; optionally set blur_kernel=3 for cleaner lines.

3. Interpret both images (understand_image on each *_bw.png):
   Ask for output as a JSON array of 9 objects, one per cell. Example prompt:
   "Describe every cell of this 3×3 grid as JSON: [{\"cell\":\"1x1\",\"edges\":[\"N\",\"S\"],\"label\":\"\"}, ...].
    edges = which sides (N/E/S/W) have a cable exit. label = plant id if visible, else empty string.
    Row 1 is top, row 3 is bottom. Column 1 is left, column 3 is right."

4. Compare & compute rotations:
   For each cell, compare current edges to target edges.
   Calculate k (0-3): how many 90° clockwise rotations transform current into target.
   Rotation rule: applying one rotation maps edge set {x} → {rotate_cw(x)} where N→E, E→S, S→W, W→N.

5. Send rotations (send_verify, one call per 90° turn):
   - task: "electricity"
   - answer: '{"rotate":"AxB"}' (JSON string — apikey is added automatically, do not include it)
   For a cell needing k rotations, call send_verify k times with the same cell id.
   Check each response for {FLG:...} — stop immediately when flag appears.

6. Verify after all rotations:
   Re-fetch the board PNG (same URL, no ?reset=1), simplify, interpret, confirm match with target.
   If mismatches remain, compute additional rotations and repeat from step 5.

7. On success ({FLG:...} in any verify response):
   Write the flag to flag.txt (fs_write, path: flag.txt). End with a text summary.

RESET (only if board is too corrupted to fix incrementally):
   fs_fetch_url with ?reset=1 appended to the board PNG URL restores the starting position.
   Then restart from step 1.
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
