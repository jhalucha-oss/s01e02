"""
Native tools: filesystem (sandboxed) + vision + wait + URL fetch.

Filesystem tools only access FS_SANDBOX_ROOT (default: ./Documentation).
"""

import base64
import json
import shutil
import time
from pathlib import Path
from urllib import error, request

from src.config import FS_SANDBOX_ROOT, PROJECT_ROOT, api
from src.helpers import logger as log
from src.helpers.api_log import append_sent_json_log
from src.native.vision import vision

# Upper bound so a single tool call cannot hang the process indefinitely.
WAIT_SECONDS_MAX = 300.0


def wait_seconds(args: dict) -> dict:
    """Sleep for the given duration (e.g. rate limits, polling backoff)."""
    raw = args["seconds"]
    try:
        seconds = float(raw)
    except (TypeError, ValueError):
        return {"error": "seconds must be a number", "seconds": raw}
    if seconds < 0:
        return {"error": "seconds must be non-negative", "seconds": seconds}
    if seconds > WAIT_SECONDS_MAX:
        return {
            "error": f"seconds must be at most {WAIT_SECONDS_MAX:g}",
            "seconds": seconds,
        }
    time.sleep(seconds)
    return {"slept_seconds": seconds, "ok": True}


MIME_BY_EXT = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


def _safe_path(relative: str) -> Path:
    """Resolve a path strictly inside FS_SANDBOX_ROOT (e.g. ./Documentation)."""
    rel = relative.replace("\\", "/").strip().lstrip("/")
    # Empty path = sandbox root (same as ".")
    rel_path = Path(".") if not rel else Path(rel)
    if rel_path.is_absolute():
        raise ValueError("Absolute paths are not allowed")
    if ".." in rel_path.parts:
        raise ValueError("Path must not contain '..'")

    root = FS_SANDBOX_ROOT.resolve()
    sandbox_name = root.name
    # Model often passes "Documentation/..." but FS_SANDBOX_ROOT already IS Documentation.
    parts = list(rel_path.parts)
    if parts and parts[0].casefold() == sandbox_name.casefold():
        rel_path = Path(*parts[1:]) if len(parts) > 1 else Path(".")

    full = (root / rel_path).resolve()
    try:
        full.relative_to(root)
    except ValueError as e:
        raise ValueError("Path escapes Documentation sandbox") from e
    return full


def _mime_for(path: Path) -> str:
    return MIME_BY_EXT.get(path.suffix.lower(), "image/jpeg")


def fs_list(args: dict) -> dict:
    path = _safe_path(args["path"])
    if not path.is_dir():
        return {"error": f"Not a directory: {args['path']}"}
    names = sorted(p.name for p in path.iterdir() if not p.name.startswith("."))
    return {"path": args["path"], "entries": names}


def fs_read(args: dict) -> dict:
    path = _safe_path(args["path"])
    if not path.is_file():
        return {"error": f"Not a file: {args['path']}"}
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    return {"path": args["path"], "content": text}


def fs_copy(args: dict) -> dict:
    src = _safe_path(args["source"])
    dst = _safe_path(args["destination"])
    if not src.is_file():
        return {"error": f"Source not a file: {args['source']}"}
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {"source": args["source"], "destination": args["destination"], "ok": True}


def fs_write(args: dict) -> dict:
    path = _safe_path(args["path"])
    if path.exists() and path.is_dir():
        return {"error": f"Path is a directory, not a file: {args['path']}"}
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(args["content"], encoding="utf-8")
    except OSError as e:
        return {"error": str(e), "path": args["path"]}
    return {"path": args["path"], "ok": True}


# Max response size for fs_fetch_url (avoid OOM on accidental huge downloads).
FETCH_URL_MAX_BYTES = 50 * 1024 * 1024

# Hub URLs may include this token; fs_fetch_url replaces it with api["AG3NTS_API_KEY"].
USER_API_KEY_URL_TAG = "#USER_API_KEY#"


def fs_fetch_url(args: dict) -> dict:
    """GET a URL and save the response body to a path inside the Documentation sandbox only (any file type, raw bytes)."""
    url = str(args["url"]).strip()
    if USER_API_KEY_URL_TAG in url:
        key = api.get("AG3NTS_API_KEY", "").strip()
        if not key:
            return {
                "error": "URL contains #USER_API_KEY# but AG3NTS_API_KEY is not configured",
                "url": url,
            }
        url = url.replace(USER_API_KEY_URL_TAG, key)
    if not url.startswith(("http://", "https://")):
        return {"error": "Only http(s) URLs are allowed", "url": url}

    path = _safe_path(args["path"])
    if path.exists() and path.is_dir():
        return {"error": f"Path is a directory, not a file: {args['path']}"}

    try:
        req = request.Request(url, method="GET")
        with request.urlopen(req, timeout=120) as resp:
            content_type = resp.headers.get("Content-Type")
            data = resp.read(FETCH_URL_MAX_BYTES + 1)
    except error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "url": url}
    except error.URLError as e:
        return {"error": str(e.reason), "url": url}

    if len(data) > FETCH_URL_MAX_BYTES:
        return {
            "error": f"Response larger than {FETCH_URL_MAX_BYTES} bytes",
            "url": url,
        }

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    except OSError as e:
        return {"error": str(e), "path": args["path"]}
    out: dict = {"path": args["path"], "bytes_written": len(data), "ok": True}
    if content_type:
        out["content_type"] = content_type
    return out


def understand_image(args: dict) -> dict:
    image_path = args["image_path"]
    question = args["question"]
    full = _safe_path(image_path)
    log.vision(image_path, question)
    try:
        if not full.is_file():
            return {"error": f"Not a file: {image_path}", "image_path": image_path}
        raw = full.read_bytes()
        b64 = base64.standard_b64encode(raw).decode("ascii")
        answer = vision(image_base64=b64, mime_type=_mime_for(full), question=question)
        log.vision_result(answer)
        return {"answer": answer, "image_path": image_path}
    except Exception as e:  # noqa: BLE001
        log.error("Vision error", str(e))
        return {"error": str(e), "image_path": image_path}


def _require_api_value(key: str) -> str:
    value = api.get(key, "")
    if not value:
        raise RuntimeError(f"Missing required config value: {key}")
    return value


def _post_json(url: str, payload: dict) -> dict:
    append_sent_json_log("_post_json", {"url": url, "body": payload})
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as http_error:
        raw = http_error.read().decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"error": raw, "status": http_error.code}
    except error.URLError as url_error:
        raise RuntimeError(f"Request failed: {url_error.reason}") from url_error


VERIFY_LOG_FILENAME = "send_verify_last.json"
POST_VERIFY_LOG_FILENAME = "post_verify_last.json"


def _write_verify_log(record: dict) -> Path:
    log_path = (PROJECT_ROOT / VERIFY_LOG_FILENAME).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record, ensure_ascii=False, indent=2)
    log_path.write_text(text, encoding="utf-8")
    return log_path


def _write_post_verify_log(record: dict) -> Path:
    log_path = (PROJECT_ROOT / POST_VERIFY_LOG_FILENAME).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return log_path


def merge_assistant_summary_into_verify_log(summary: str) -> None:
    """Append the final model message after send_verify into the same JSON file."""
    path = (PROJECT_ROOT / VERIFY_LOG_FILENAME).resolve()
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}
    data["assistantSummary"] = summary
    try:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info(f"Zapisano podsumowanie modelu w {path}")
    except OSError as e:
        log.error("Nie udało się dopisać assistantSummary", str(e))


def send_verify(args: dict) -> dict:
    task = str(args["task"]).strip()
    raw_answer = args["answer"]
    if not isinstance(raw_answer, str):
        return {"error": "answer must be a JSON string", "answer": raw_answer}
    try:
        answer = json.loads(raw_answer)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in answer: {e}", "answer": raw_answer}

    request_error: str | None = None
    response: dict | None = None

    try:
        payload = {
            "apikey": _require_api_value("AG3NTS_API_KEY"),
            "task": task,
            "answer": answer,
        }
        response = _post_json(_require_api_value("verify_api_endpoint"), payload)
    except Exception as e:  # noqa: BLE001
        request_error = str(e)

    record: dict = {
        "sentAnswer": answer,
        "request": {"task": task, "answer": answer},
        "verifyResponse": response,
    }
    if request_error is not None:
        record["requestError"] = request_error

    try:
        log_path = _write_verify_log(record)
        log.info(f"Zapisano log weryfikacji: {log_path}")
    except OSError as e:
        log.error("Nie udało się zapisać pliku logu", str(e))
        err_body: dict = {
            "success": False,
            "sentAnswer": answer,
            "verifyResponse": response,
            "saveError": str(e),
        }
        if request_error is not None:
            err_body["requestError"] = request_error
        return err_body

    out: dict = {
        "success": request_error is None,
        "sentAnswer": answer,
        "verifyResponse": response,
        "savedTo": str(log_path),
    }
    if request_error is not None:
        out["requestError"] = request_error
    return out


def post_verify_json(args: dict) -> dict:
    """POST arbitrary JSON fields to the verify hub; apikey from config is merged into the body (always wins)."""
    raw = args["body_json"]
    if isinstance(raw, dict):
        body = raw
    else:
        if not isinstance(raw, str):
            return {"error": "body_json must be a JSON object or a JSON string", "body_json": raw}
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {e}", "body_json": raw}
        if not isinstance(parsed, dict):
            return {"error": "body_json must decode to a JSON object", "parsed": parsed}
        body = parsed

    request_error: str | None = None
    response: dict | None = None
    payload = {**body, "apikey": _require_api_value("AG3NTS_API_KEY")}

    try:
        response = _post_json(_require_api_value("verify_api_endpoint"), payload)
    except Exception as e:  # noqa: BLE001
        request_error = str(e)

    record: dict = {
        "requestBody": body,
        "requestWithApikey": {k: ("<redacted>" if k == "apikey" else v) for k, v in payload.items()},
        "verifyResponse": response,
    }
    if request_error is not None:
        record["requestError"] = request_error

    try:
        log_path = _write_post_verify_log(record)
        log.info(f"Zapisano log POST verify: {log_path}")
    except OSError as e:
        log.error("Nie udało się zapisać pliku logu post_verify", str(e))
        err_body: dict = {
            "success": False,
            "sentBody": body,
            "verifyResponse": response,
            "saveError": str(e),
        }
        if request_error is not None:
            err_body["requestError"] = request_error
        return err_body

    out: dict = {
        "success": request_error is None,
        "sentBody": body,
        "verifyResponse": response,
        "savedTo": str(log_path),
    }
    if request_error is not None:
        out["requestError"] = request_error
    return out


native_tools = [
    {
        "type": "function",
        "name": "fs_list",
        "description": (
            "List file and folder names in a directory. "
            "Path is relative to the Documentation sandbox only (not the whole project)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory under Documentation/, e.g. docs/ or . for the sandbox root.",
                },
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "fs_read",
        "description": "Read a UTF-8 text file inside the Documentation sandbox.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path under Documentation/, e.g. docs/index.md."},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "fs_copy",
        "description": "Copy a file inside the Documentation sandbox. Creates parent dirs if needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source path under Documentation/."},
                "destination": {
                    "type": "string",
                    "description": "Destination path under Documentation/.",
                },
            },
            "required": ["source", "destination"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "fs_write",
        "description": (
            "Create or overwrite a UTF-8 text file inside the Documentation sandbox only. "
            "Creates parent directories if needed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path under Documentation/, e.g. docs/notes.md.",
                },
                "content": {
                    "type": "string",
                    "description": "Full file body to write (UTF-8).",
                },
            },
            "required": ["path", "content"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "fs_fetch_url",
        "description": (
            "Download any file from an http(s) URL (GET) and save it under the Documentation sandbox only — "
            "same path rules as fs_read/fs_write (no paths outside Documentation). "
            "Extension and content are not validated; response body is written as raw bytes. "
            f"Maximum download size {FETCH_URL_MAX_BYTES // (1024 * 1024)} MiB per call."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": (
                        "Full http or https URL of the resource to download. "
                        "If the URL contains the literal #USER_API_KEY#, it is replaced with the configured AG3NTS_API_KEY before the request."
                    ),
                },
                "path": {
                    "type": "string",
                    "description": (
                        "Destination file path relative to Documentation/ only, e.g. downloads/data.zip or assets/chart.png."
                    ),
                },
            },
            "required": ["url", "path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "understand_image",
        "description": (
            "Analyze an image and answer questions about it. "
            "Use to identify people, objects, scenes, or visual traits."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Path under Documentation/, e.g. docs/attachment.png",
                },
                "question": {
                    "type": "string",
                    "description": "What to determine from the image.",
                },
            },
            "required": ["image_path", "question"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "wait_seconds",
        "description": (
            "Pause execution for a given number of seconds. "
            "Use for rate limits, delays between API retries, or polling backoff. "
            f"Maximum {WAIT_SECONDS_MAX:g} seconds per call."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "seconds": {
                    "type": "number",
                    "description": "How long to sleep, in seconds (fractional values allowed).",
                },
            },
            "required": ["seconds"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "post_verify_json",
        "description": (
            "POST a JSON body to the same verify hub URL as send_verify. "
            "Provide task/answer (and any other fields) as JSON; apikey from config is merged in and overrides any apikey in the payload. "
            "Use for railway and other tasks. Response is logged to post_verify_last.json."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "body_json": {
                    "type": "string",
                    "description": (
                        'Stringified JSON object for the request body, e.g. '
                        '{"task":"railway","answer":{"action":"help"}}. Do not include apikey.'
                    ),
                },
            },
            "required": ["body_json"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "send_verify",
        "description": (
            "POST to the verify hub with apikey from config: task name plus answer as JSON. "
            "For tasks that require many steps (e.g. electricity: one POST per 90° tile rotation), call as many times as needed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Verify task name, e.g. sendit, categorize, railway.",
                },
                "answer": {
                    "type": "string",
                    "description": (
                        "Stringified JSON value for the answer field (object, array, or scalar), "
                        'e.g. {"prompt":"..."} or {"declaration":"..."}.'
                    ),
                },
            },
            "required": ["task", "answer"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]

_NATIVE_HANDLERS = {
    "fs_list": fs_list,
    "fs_read": fs_read,
    "fs_copy": fs_copy,
    "fs_write": fs_write,
    "fs_fetch_url": fs_fetch_url,
    "understand_image": understand_image,
    "wait_seconds": wait_seconds,
    "post_verify_json": post_verify_json,
    "send_verify": send_verify,
}


def execute_native_tool(name: str, args: dict) -> dict:
    handler = _NATIVE_HANDLERS.get(name)
    if not handler:
        raise RuntimeError(f"Unknown tool: {name}")
    return handler(args)
