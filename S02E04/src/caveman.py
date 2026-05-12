"""Optional caveman-style compression for agent instructions."""

import os

CAVEMAN_MODE_ENV = "CAVEMAN_MODE"
DEFAULT_MODE = "off"
SUPPORTED_MODES = {"off", "lite", "full", "ultra"}

_MODE_RULES = {
    "lite": (
        "Use concise, professional answers. Drop filler, pleasantries, "
        "and hedging. Keep normal grammar where it helps clarity."
    ),
    "full": (
        "Respond terse like smart caveman. Drop articles and filler. "
        "Fragments are OK. Keep all technical facts exact."
    ),
    "ultra": (
        "Respond in ultra-compact fragments. Use arrows for causality "
        "where clear. Do not abbreviate code symbols, JSON keys, flags, "
        "API names, or exact error text."
    ),
}


def get_caveman_mode() -> str:
    """Read and validate the optional caveman mode."""
    mode = os.getenv(CAVEMAN_MODE_ENV, DEFAULT_MODE).strip().lower()
    if mode not in SUPPORTED_MODES:
        allowed = ", ".join(sorted(SUPPORTED_MODES))
        raise RuntimeError(f"{CAVEMAN_MODE_ENV} must be one of: {allowed}")
    return mode


def build_caveman_instructions(mode: str | None = None) -> str:
    """Return the prompt suffix for the requested compression mode."""
    selected_mode = get_caveman_mode() if mode is None else mode.strip().lower()
    if selected_mode == "off":
        return ""
    if selected_mode not in _MODE_RULES:
        allowed = ", ".join(sorted(SUPPORTED_MODES))
        raise RuntimeError(f"caveman mode must be one of: {allowed}")

    return f"""

CAVEMAN OUTPUT MODE ({selected_mode})
 - {_MODE_RULES[selected_mode]}
 - Compression applies only to assistant prose.
 - Do not compress or alter code blocks, JSON payloads, tool arguments,
   filesystem paths, URLs, flags, timestamps, component ids, or quoted errors.
 - If brevity could make a destructive action, security warning, or ordered
   workflow ambiguous, use normal clear wording for that part.
"""


def append_caveman_instructions(base_instructions: str) -> str:
    """Append caveman instructions when CAVEMAN_MODE is enabled."""
    return base_instructions.rstrip() + build_caveman_instructions()
