"""Append sent JSON payloads to project logs.txt (timestamp per line)."""

import json
from datetime import datetime, timezone
from typing import Any

from src.config import PROJECT_ROOT

LOGS_PATH = PROJECT_ROOT / "logs.txt"


def _redact_for_log(obj: Any) -> Any:
    """Redact secrets and huge binary payloads for safe logging."""
    if isinstance(obj, dict):
        return {
            k: ("<redacted>" if k == "apikey" else _redact_for_log(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact_for_log(x) for x in obj]
    if isinstance(obj, str):
        if ";base64," in obj or (len(obj) > 2000 and obj.startswith("data:")):
            return f"<omitted {len(obj)} chars>"
        if len(obj) > 50000:
            return f"<omitted {len(obj)} chars>"
        return obj
    return obj


def append_sent_json_log(source: str, payload: Any) -> None:
    """Append exactly one line: ISO date, source label, compact single-line JSON (redacted)."""
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    safe = _redact_for_log(payload)
    try:
        text = json.dumps(safe, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError):
        text = repr(safe).replace("\n", " ").replace("\r", " ")
    if "\n" in text or "\r" in text:
        text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    line = f"{ts} {source} {text}\n"
    try:
        LOGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOGS_PATH.open("a", encoding="utf-8") as f:
            f.write(line)
    except OSError:
        pass
