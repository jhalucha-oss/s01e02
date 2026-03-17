import shutil

from src.config import sandbox


def initialize_sandbox() -> None:
    shutil.rmtree(sandbox["root"], ignore_errors=True)
    sandbox["root"].mkdir(parents=True, exist_ok=True)


def resolve_sandbox_path(relative_path: str):
    sandbox_root = sandbox["root"].resolve()
    resolved = (sandbox_root / relative_path).resolve()

    try:
        resolved.relative_to(sandbox_root)
    except ValueError as error:
        raise RuntimeError(
            f'Access denied: path "{relative_path}" is outside sandbox'
        ) from error

    return resolved
