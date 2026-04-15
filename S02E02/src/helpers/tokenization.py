"""Token counts for prompts and chat-style messages (OpenAI-compatible via tiktoken)."""

from __future__ import annotations

import json
from typing import Any

try:
    import tiktoken
except ImportError:
    tiktoken = None  # type: ignore[misc, assignment]

from src.config import api


def _estimate_tokens_heuristic(text: str) -> int:
    """
    Rough token estimate when tiktoken is unavailable (~4 UTF-8 bytes per token).
    Less accurate than tiktoken; install tiktoken for exact counts.
    """
    if not text:
        return 0
    return max(1, (len(text.encode("utf-8")) + 3) // 4)


def _get_encoding(model: str | None):
    """Return tiktoken Encoding or None if tiktoken missing / unsupported."""
    if tiktoken is None:
        return None
    name = (model or api["model"]).strip()
    try:
        return tiktoken.encoding_for_model(name)
    except KeyError:
        try:
            return tiktoken.get_encoding("o200k_base")
        except Exception:
            return None


def encoding_for_model(model: str | None = None):
    """
    Return tiktoken encoding for the model, or raise if tiktoken cannot be used.
    Prefer using ``count_tokens_*`` helpers, which fall back to a heuristic when needed.
    """
    enc = _get_encoding(model)
    if enc is None:
        raise RuntimeError(
            "tiktoken is not available. Install with: pip install tiktoken "
            "(requires a wheel for your Python version), or use count_* functions "
            "which fall back to a byte-based heuristic."
        )
    return enc


def count_tokens_text(text: str, *, model: str | None = None) -> int:
    """Count tokens in a plain string (prompt or fragment)."""
    enc = _get_encoding(model)
    if enc is not None:
        return len(enc.encode(text))
    return _estimate_tokens_heuristic(text)


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                parts.append(str(block))
                continue
            btype = block.get("type", "")
            if btype in ("input_text", "text", "output_text"):
                parts.append(str(block.get("text", "")))
            elif btype == "input_image":
                parts.append("[image]")
            else:
                parts.append(json.dumps(block, ensure_ascii=False))
        return "\n".join(parts)
    return str(content)


def _encode_len(s: str, enc) -> int:
    if enc is None:
        return _estimate_tokens_heuristic(s)
    return len(enc.encode(s))


def _message_token_estimate(msg: dict, enc) -> int:
    """Per-message overhead + encoded payload (approximate for Responses/chat-style items)."""
    overhead = 4
    t = msg.get("type")
    if t in ("function_call", "function_call_output"):
        return overhead + _encode_len(json.dumps(msg, ensure_ascii=False), enc)
    role = str(msg.get("role", ""))
    n = overhead + _encode_len(role, enc) + _encode_len(_content_to_text(msg.get("content")), enc)
    for key in ("name", "tool_call_id", "call_id"):
        if key in msg:
            n += _encode_len(str(msg[key]), enc)
    return n


def count_tokens_single_message(msg: Any, *, model: str | None = None) -> int:
    """Token estimate for one chat/Responses item (same rules as ``count_tokens_messages``)."""
    enc = _get_encoding(model)
    if isinstance(msg, dict):
        return _message_token_estimate(msg, enc)
    if enc is not None:
        return len(enc.encode(str(msg)))
    return _estimate_tokens_heuristic(str(msg))


def count_tokens_messages(messages: list, *, model: str | None = None) -> int:
    """
    Approximate total tokens for a list of OpenAI-style / Responses API items
    (role+content, function_call, function_call_output, etc.).
    """
    enc = _get_encoding(model)
    total = 2
    for msg in messages:
        if isinstance(msg, dict):
            total += _message_token_estimate(msg, enc)
        elif enc is not None:
            total += len(enc.encode(str(msg)))
        else:
            total += _estimate_tokens_heuristic(str(msg))
    return total


def count_tokens_tools(tools: list | None, *, model: str | None = None) -> int:
    """Token count for serialized tools schema (as sent in API body)."""
    if not tools:
        return 0
    return count_tokens_text(json.dumps(tools, ensure_ascii=False), model=model)


def tokenization_report(
    *,
    text: str | None = None,
    input_messages: list | None = None,
    instructions: str | None = None,
    tools: list | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Aggregate token estimate for a chat request (same pieces as ``api.chat``).

    Returns counts per part, ``total``, and ``method`` (``\"tiktoken\"`` or ``\"heuristic\"``).
    Message/tool totals are approximate even with tiktoken (format overhead differs from API).
    """
    m = model or api["model"]
    enc = _get_encoding(m)
    method = "tiktoken" if enc is not None else "heuristic"
    parts: dict[str, int] = {}
    if text is not None:
        parts["text"] = count_tokens_text(text, model=m)
    if input_messages is not None:
        parts["messages"] = count_tokens_messages(input_messages, model=m)
    if instructions:
        parts["instructions"] = count_tokens_text(instructions, model=m)
    if tools is not None:
        parts["tools"] = count_tokens_tools(tools, model=m)
    total = sum(parts.values())
    return {"model": m, "method": method, "parts": parts, "total": total}
