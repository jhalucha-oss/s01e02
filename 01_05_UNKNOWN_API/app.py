"""
Image Recognition Agent (Python)
--------------------------------
Fake report generation agent.
"""

import sys
from pathlib import Path

# Allow `python app.py` from project root without installing a package
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.agent import run
from src.helpers import logger as log
from src.helpers.stats import log_stats

DOCUMENT_QUERY = """Process the railway API and activate the route.
Start by calling the "help" action to retrieve the full API documentation. Carefully read and follow all instructions provided by the API, including available actions, required parameters, and the correct sequence of steps.
Execute the required actions step-by-step to activate the railway route X-01. Handle 503 errors by retrying requests with appropriate delays, and respect all rate limits indicated in response headers.
Continue interacting with the API until the route is successfully activated and the system returns a flag.
Submit all requests to the /verify endpoint as required."""


def main() -> None:
    log.box("Image Recognition Agent\nFake report generation agent.")
    log.start("Starting image Fake report generation...")
    try:
        result = run(DOCUMENT_QUERY)
        log.success("Classification complete")
        log.info(result["response"])
        log_stats()
    except Exception as e:  # noqa: BLE001
        log.error("Run failed", str(e))
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
