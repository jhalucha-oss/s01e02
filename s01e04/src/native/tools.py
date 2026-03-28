"""
Native tools: filesystem (replaces MCP files server) + vision.
"""

import base64
import shutil
from pathlib import Path

from src.config import PROJECT_ROOT
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
    rel = relative.replace("\\", "/").lstrip("/")
    root = PROJECT_ROOT.resolve()
    full = (root / rel).resolve()
    try:
        full.relative_to(root)
    except ValueError as e:
        raise ValueError("Path escapes project root") from e
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


native_tools = [
    {
        "type": "function",
        "name": "fs_list",
        "description": "List file and folder names in a directory relative to project root.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path, e.g. knowledge/ or images/",
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
        "description": "Read a UTF-8 text file relative to project root.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path relative to project root."},
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "fs_copy",
        "description": "Copy a file. Creates parent directories for the destination if needed.",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source file path relative to project root."},
                "destination": {
                    "type": "string",
                    "description": "Destination file path relative to project root.",
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
                    "description": "Path relative to project root, e.g. images/photo.jpg",
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
]

_NATIVE_HANDLERS = {
    "fs_list": fs_list,
    "fs_read": fs_read,
    "fs_copy": fs_copy,
    "understand_image": understand_image,
}


def execute_native_tool(name: str, args: dict) -> dict:
    handler = _NATIVE_HANDLERS.get(name)
    if not handler:
        raise RuntimeError(f"Unknown tool: {name}")
    return handler(args)
