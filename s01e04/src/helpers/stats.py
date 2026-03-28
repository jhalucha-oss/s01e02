"""Token usage statistics."""

_total = {"input": 0, "output": 0, "requests": 0}


def record_usage(usage: dict | None) -> None:
    if not usage:
        return
    _total["input"] += int(usage.get("input_tokens") or 0)
    _total["output"] += int(usage.get("output_tokens") or 0)
    _total["requests"] += 1


def get_stats() -> dict[str, int]:
    return dict(_total)


def log_stats() -> None:
    i, o, r = _total["input"], _total["output"], _total["requests"]
    print(f"\n📊 Stats: {r} requests, {i} input tokens, {o} output tokens, {i + o} total\n")


def reset_stats() -> None:
    _total["input"] = 0
    _total["output"] = 0
    _total["requests"] = 0
