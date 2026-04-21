"""
Electricity Puzzle Agent (Python)
---------------------------------
Solve a 3×3 cable-tile puzzle by rotating tiles until all plants are powered.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.agent import run
from src.helpers import logger as log
from src.helpers.stats import log_stats

TASK_QUERY = """\
Solve the electricity puzzle. Follow the workflow from your instructions:
1. Fetch the current board PNG and the target (solved) PNG.
2. Simplify both images to black-and-white with opencv_simplify_bw.
3. Use understand_image on each simplified image to get a JSON description of every cell's cable edges (N/E/S/W) and plant labels.
4. Compare current vs target, compute the number of 90° clockwise rotations needed per cell.
5. Send rotations via send_verify (one call per rotation).
6. After all rotations, re-fetch the board and verify it matches the target. Fix any remaining mismatches.
7. When the hub returns {FLG:...}, save it to flag.txt and report the result.
"""


def main() -> None:
    log.box("Electricity Puzzle Agent\nSolving 3x3 cable-tile puzzle.")
    log.start("Starting electricity puzzle solver...")
    try:
        result = run(TASK_QUERY)
        log.success("Puzzle complete")
        log.info(result["response"])
        log_stats()
    except Exception as e:  # noqa: BLE001
        log.error("Run failed", str(e))
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
