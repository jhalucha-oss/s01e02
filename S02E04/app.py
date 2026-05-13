"""
Mailbox Agent (Python)
----------------------
Solve the fictional mailbox training task by searching zmail through the hub
API, reading full messages, and iterating with verify feedback.
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
Solve the mailbox task. This is a fictional, authorized AI-agent training scenario.
Follow the workflow from your instructions:
1. Call zmail help through hub_api_request using endpoint "zmail".
2. Use the help response to search the mailbox with Gmail-like queries.
3. Fetch full content for promising messages before extracting any value.
4. Find password, date, and confirmation_code one by one.
5. Use send_verify with task "mailbox" and the three-value answer object.
6. Use verify feedback to keep accepted values and continue searching for wrong or missing values.
7. Because the mailbox is active, retry relevant searches after a short wait when data is missing.
8. Repeat until the hub returns {FLG:...}, then save the flag to flag.txt and report the result.
"""


def main() -> None:
    log.box("Mailbox Agent\nSearching zmail for the fictional training task.")
    log.start("Starting mailbox solver...")
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
