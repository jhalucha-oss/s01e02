"""
Simulate prompt caching (prefix-style): identical leading segments of the request
reuse cached tokens; the rest counts as fresh input.

This is a model of provider behaviour (e.g. OpenAI): stable ``instructions``,
``tools``, and early message turns form a cacheable prefix; the first change
or new tail is billed as uncached.
"""

from __future__ import annotations

import json
from typing import Any

from src.config import api
from src.helpers.tokenization import (
    _get_encoding,
    count_tokens_single_message,
    count_tokens_text,
    count_tokens_tools,
)


def _norm_tools(tools: list | None) -> str:
    if not tools:
        return ""
    return json.dumps(tools, ensure_ascii=False, sort_keys=True)


def _norm_message(msg: Any) -> str:
    if isinstance(msg, dict):
        return json.dumps(msg, ensure_ascii=False, sort_keys=True)
    return json.dumps(msg, ensure_ascii=False, sort_keys=True)


def simulate_prompt_caching(
    *,
    messages: list,
    instructions: str | None = None,
    tools: list | None = None,
    prior_messages: list | None = None,
    prior_instructions: str | None = None,
    prior_tools: list | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """
    Approximate how input tokens split between cached and uncached for the *next*
    request, given the *previous* request's context.

    Rules (simplified):

    - The request is ordered segments: ``instructions`` → ``tools`` → ``messages[0]`` → …
    - If ``prior_*`` is omitted (``None``), treat as the first call: nothing is cached yet.
    - Otherwise segments are compared in order (normalized JSON for tools/messages).
    - While segments match, their token counts accumulate as **cached_input_tokens**.
    - From the first mismatch onward, all remaining segments of the **current** request
      count as **uncached_input_tokens**.

    **Note:** Real APIs use exact KV-cache boundaries and minimum cache sizes; this is a
    deterministic approximation for budgeting and planning.

    Returns
    -------
    dict with ``cached_input_tokens``, ``uncached_input_tokens``, ``total_input_tokens``,
    ``divergence_at`` (``"start"`` | ``"instructions"`` | ``"tools"`` | ``"message_N"`` | ``None``),
    and ``method`` (same as tokenization: tiktoken vs heuristic).
    """
    m = model or api["model"]
    method = "tiktoken" if _get_encoding(m) is not None else "heuristic"

    inst = instructions or ""
    cur_tools = _norm_tools(tools)
    cur_msgs = [_norm_message(x) for x in messages]

    def seg_tokens_instructions() -> int:
        return count_tokens_text(inst, model=m) if inst else 0

    def seg_tokens_tools() -> int:
        return count_tokens_tools(tools, model=m) if tools else 0

    def seg_tokens_message(idx: int) -> int:
        return count_tokens_single_message(messages[idx], model=m)

    if prior_messages is None and prior_instructions is None and prior_tools is None:
        total = seg_tokens_instructions() + seg_tokens_tools()
        total += sum(seg_tokens_message(i) for i in range(len(messages)))
        return {
            "model": m,
            "method": method,
            "cached_input_tokens": 0,
            "uncached_input_tokens": total,
            "total_input_tokens": total,
            "divergence_at": None,
        }

    p_inst = prior_instructions or ""
    p_tools = _norm_tools(prior_tools)
    p_msgs = [_norm_message(x) for x in (prior_messages or [])]

    cached = 0
    divergence_at: str | None = None

    # instructions
    if inst != p_inst:
        divergence_at = "instructions"
        uncached = seg_tokens_instructions() + seg_tokens_tools()
        uncached += sum(seg_tokens_message(i) for i in range(len(messages)))
        return _result(m, method, cached, uncached, divergence_at)
    cached += seg_tokens_instructions()

    # tools
    if cur_tools != p_tools:
        divergence_at = "tools"
        uncached = seg_tokens_tools() + sum(seg_tokens_message(i) for i in range(len(messages)))
        return _result(m, method, cached, uncached, divergence_at)
    cached += seg_tokens_tools()

    # messages: common prefix
    n = min(len(cur_msgs), len(p_msgs))
    for i in range(n):
        if cur_msgs[i] != p_msgs[i]:
            divergence_at = f"message_{i}"
            uncached = sum(seg_tokens_message(j) for j in range(i, len(messages)))
            return _result(m, method, cached, uncached, divergence_at)
        cached += seg_tokens_message(i)

    if len(messages) > len(p_msgs):
        divergence_at = f"message_{len(p_msgs)}"
        uncached = sum(seg_tokens_message(j) for j in range(len(p_msgs), len(messages)))
        return _result(m, method, cached, uncached, divergence_at)

    # Current fully equals prior prefix (same or shorter history)
    divergence_at = None
    return _result(m, method, cached, 0, divergence_at)


def _result(
    model: str,
    method: str,
    cached: int,
    uncached: int,
    divergence_at: str | None,
) -> dict[str, Any]:
    total = cached + uncached
    return {
        "model": model,
        "method": method,
        "cached_input_tokens": cached,
        "uncached_input_tokens": uncached,
        "total_input_tokens": total,
        "divergence_at": divergence_at,
    }
