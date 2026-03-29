"""
Native tools: filesystem (sandboxed) + vision.

Filesystem tools only access FS_SANDBOX_ROOT (default: ./Documentation).
"""

import base64
import json
import shutil
from pathlib import Path
from urllib import error, request

from src.config import FS_SANDBOX_ROOT, PROJECT_ROOT, api
from src.helpers import logger as log
from src.native.vision import vision

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


def _write_verify_log(record: dict) -> Path:
    log_path = (PROJECT_ROOT / VERIFY_LOG_FILENAME).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record, ensure_ascii=False, indent=2)
    log_path.write_text(text, encoding="utf-8")
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
    answer = {"declaration": args["declaration"]}
    request_error: str | None = None
    response: dict | None = None

    try:
        payload = {
            "apikey": _require_api_value("AG3NTS_API_KEY"),
            "task": "sendit",
            "answer": answer,
        }
        response = _post_json(_require_api_value("verify_api_endpoint"), payload)
    except Exception as e:  # noqa: BLE001
        request_error = str(e)

    record: dict = {
        "sentAnswer": answer,
        "request": {"task": "sendit", "answer": answer},
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
        "name": "send_verify",
        "description": (
            "Send the final answer for the sendit task to the verify endpoint."
            "Call at most 5 times per conversation — after these 15 runs, no more tool calls are allowed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "declaration": {
                    "type": "string",
                    "description": "Final answear of the task - whole declaration text",
                }
            },
            "required": ["declaration"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]

_NATIVE_HANDLERS = {
    "fs_list": fs_list,
    "fs_read": fs_read,
    "fs_copy": fs_copy,
    "understand_image": understand_image,
    "send_verify": send_verify,
}


def execute_native_tool(name: str, args: dict) -> dict:
    handler = _NATIVE_HANDLERS.get(name)
    if not handler:
        raise RuntimeError(f"Unknown tool: {name}")
    return handler(args)
