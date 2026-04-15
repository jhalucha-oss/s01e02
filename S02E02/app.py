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

DOCUMENT_QUERY = """Classify each item as DNG (dangerous) or NEU (neutral) based on its description. 
    Always label reactor-related items (e.g., reactor parts, fuel, or components) as NEU, even if they seem dangerous. For all other items, 
    classify according to risk. Use instructions to resolve that task Use classifing api to classify items. retry this operation max 8 times and every time adjus ptompting."""


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
