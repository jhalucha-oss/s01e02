from datetime import datetime, timezone

from src.utils.sandbox import resolve_sandbox_path


def _to_iso(timestamp: float) -> str:
    return (
        datetime.fromtimestamp(timestamp, tz=timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def list_files(args):
    full_path = resolve_sandbox_path(args["path"])
    return [
        {
            "name": entry.name,
            "type": "directory" if entry.is_dir() else "file",
        }
        for entry in full_path.iterdir()
    ]


def read_file(args):
    full_path = resolve_sandbox_path(args["path"])
    return {"content": full_path.read_text(encoding="utf-8")}


def write_file(args):
    full_path = resolve_sandbox_path(args["path"])
    full_path.write_text(args["content"], encoding="utf-8")
    return {"success": True, "message": f"File written: {args['path']}"}


def delete_file(args):
    full_path = resolve_sandbox_path(args["path"])
    full_path.unlink()
    return {"success": True, "message": f"File deleted: {args['path']}"}


def create_directory(args):
    full_path = resolve_sandbox_path(args["path"])
    full_path.mkdir(parents=True, exist_ok=True)
    return {"success": True, "message": f"Directory created: {args['path']}"}


def file_info(args):
    full_path = resolve_sandbox_path(args["path"])
    stats = full_path.stat()
    return {
        "size": stats.st_size,
        "isDirectory": full_path.is_dir(),
        "created": _to_iso(stats.st_ctime),
        "modified": _to_iso(stats.st_mtime),
    }


handlers = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "delete_file": delete_file,
    "create_directory": create_directory,
    "file_info": file_info,
}


