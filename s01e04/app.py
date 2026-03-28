"""
Image Recognition Agent (Python)
--------------------------------
Classifies images in images/ using profiles in knowledge/, writes to images/organized/.
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

CLASSIFICATION_QUERY = """Classify all images in the images/ folder based on the character knowledge files.
Read the knowledge files first, then analyze each image and copy it to the appropriate character folder(s)."""


def main() -> None:
    log.box("Image Recognition Agent\nClassify images by character")
    log.start("Starting image classification...")
    try:
        result = run(CLASSIFICATION_QUERY)
        log.success("Classification complete")
        log.info(result["response"])
        log_stats()
    except Exception as e:  # noqa: BLE001
        log.error("Run failed", str(e))
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
