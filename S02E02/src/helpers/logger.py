"""Terminal logger (ANSI colors)."""

from datetime import datetime


class Colors:
    reset = "\x1b[0m"
    bright = "\x1b[1m"
    dim = "\x1b[2m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    magenta = "\x1b[35m"
    cyan = "\x1b[36m"
    white = "\x1b[37m"
    bg_blue = "\x1b[44m"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def info(msg: str) -> None:
    print(f"{Colors.dim}[{_ts()}]{Colors.reset} {msg}")


def success(msg: str) -> None:
    print(f"{Colors.dim}[{_ts()}]{Colors.reset} {Colors.green}✓{Colors.reset} {msg}")


def error(title: str, msg: str = "") -> None:
    print(f"{Colors.dim}[{_ts()}]{Colors.reset} {Colors.red}✗ {title}{Colors.reset} {msg}")


def start(msg: str) -> None:
    print(f"{Colors.dim}[{_ts()}]{Colors.reset} {Colors.cyan}→{Colors.reset} {msg}")


def box(text: str) -> None:
    lines = text.split("\n") or [""]
    width = max(len(l) for l in lines) + 4
    print(f"\n{Colors.cyan}{'─' * width}{Colors.reset}")
    for line in lines:
        pad = width - 3 - len(line)
        print(
            f"{Colors.cyan}│{Colors.reset} {Colors.bright}{line}{' ' * max(0, pad)}{Colors.reset}{Colors.cyan}│{Colors.reset}"
        )
    print(f"{Colors.cyan}{'─' * width}{Colors.reset}\n")


def query(q: str) -> None:
    print(f"\n{Colors.bg_blue}{Colors.white} QUERY {Colors.reset} {q}\n")


def api_step(step: str, msg_count: int) -> None:
    print(f"{Colors.dim}[{_ts()}]{Colors.reset} {Colors.magenta}◆{Colors.reset} {step} ({msg_count} messages)")


def api_done(usage: dict | None) -> None:
    if usage:
        inp = usage.get("input_tokens", 0)
        out = usage.get("output_tokens", 0)
        print(f"{Colors.dim}         tokens: {inp} in / {out} out{Colors.reset}")


def tool(name: str, args: dict) -> None:
    s = str(args)
    if len(s) > 100:
        s = s[:100] + "..."
    print(f"{Colors.dim}[{_ts()}]{Colors.reset} {Colors.yellow}⚡{Colors.reset} {name} {Colors.dim}{s}{Colors.reset}")


def tool_result(name: str, ok: bool, output: str) -> None:
    icon = f"{Colors.green}✓{Colors.reset}" if ok else f"{Colors.red}✗{Colors.reset}"
    if len(output) > 150:
        output = output[:150] + "..."
    print(f"{Colors.dim}         {icon} {output}{Colors.reset}")


def vision(path: str, question: str) -> None:
    print(f"{Colors.dim}[{_ts()}]{Colors.reset} {Colors.blue}👁{Colors.reset} Vision: {path}")
    print(f"{Colors.dim}         Q: {question}{Colors.reset}")


def vision_result(answer: str) -> None:
    if len(answer) > 200:
        answer = answer[:200] + "..."
    print(f"{Colors.dim}         A: {answer}{Colors.reset}")
