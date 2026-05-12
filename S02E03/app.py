"""
Failure Log Agent (Python)
--------------------------
Filter a large power-plant log file to <=1500 tokens and iteratively
submit it to the verification hub until the flag is returned.
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
Solve the failure task. Follow the workflow from your instructions:
1. Fetch the power-plant log file from the hub.
2. Read the file once and filter only WARN/ERRO/CRIT lines related to plant subsystems.
3. Build a condensed log string (one event per line, timestamp + severity + component + short description).
4. Verify the string is under 6000 characters before sending.
5. Send via send_verify with task "failure" and answer {"logs": "<condensed string>"}.
6. Read the feedback — add any missing components identified by Centrala, recheck budget, re-send.
7. Repeat until the hub returns {FLG:...}, then save the flag to flag.txt and report the result.
"""


def main() -> None:
    log.box("Failure Log Agent\nFiltering power-plant logs for failure analysis.")
    log.start("Starting failure log solver...")
    try:
        result = run(TASK_QUERY)
        log.success("Task complete")
        log.info(result["response"])
        log_stats()
    except Exception as e:  # noqa: BLE001
        log.error("Run failed", str(e))
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
