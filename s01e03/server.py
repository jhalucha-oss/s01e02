"""
s01e03 – Proxy HTTP Server
--------------------------
Endpoint: POST /
Body JSON: { "sessionID": "...", "question": "..." }

The server maintains per-session conversation history and uses the LLM
with function calling (check_package / redirect_package) to handle requests.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer

from src.api import chat, extract_text, extract_tool_calls
from src.config import api
from src.tools import handlers, tools


MAX_TOOL_ROUNDS = 20

# { sessionID -> list of conversation messages }
_sessions: dict[str, list] = {}


def _process_message(session_id: str, question: str) -> str:
    """Run one user turn through the LLM function-calling loop."""
    history = _sessions.setdefault(session_id, [])

    history.append({"role": "user", "content": question})

    for _ in range(MAX_TOOL_ROUNDS):
        response = chat(
            model=api["model"],
            input=history,
            tools=tools,
            instructions=api["instructions"],
        )
        tool_calls = extract_tool_calls(response)

        if not tool_calls:
            answer = extract_text(response) or "Brak odpowiedzi"
            history.append({"role": "assistant", "content": answer})
            return answer

        # Execute tool calls and append results to history
        results = []
        for call in tool_calls:
            args = json.loads(call["arguments"])
            print(f"  -> {call['name']}({json.dumps(args, ensure_ascii=False)})")
            try:
                result = handlers[call["name"]](args)
                print(f"     OK: {result}")
            except Exception as exc:  # noqa: BLE001
                result = {"error": str(exc)}
                print(f"     ERR: {exc}")
            results.append(
                {
                    "type": "function_call_output",
                    "call_id": call["call_id"],
                    "output": json.dumps(result),
                }
            )

        history.extend(tool_calls)
        history.extend(results)

    return "Przekroczono limit wywołań narzędzi"


class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # noqa: ANN001
        print(f"[HTTP] {fmt % args}")

    def _send_json(self, status: int, data: dict) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):  # noqa: N802
        if self.path != "/":
            self._send_json(404, {"error": "Not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        try:
            payload = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        session_id = payload.get("sessionID")
        question = payload.get("question")

        if not session_id or not question:
            self._send_json(400, {"error": "Missing sessionID or question"})
            return

        print(f"\n[{session_id}] Q: {question}")
        answer = _process_message(session_id, question)
        print(f"[{session_id}] A: {answer}")

        self._send_json(200, {"reply": answer})

    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_json(404, {"error": "Not found"})


def main() -> None:
    host = "0.0.0.0"
    port = 8000
    server = HTTPServer((host, port), ProxyHandler)
    print(f"Server running on http://{host}:{port}")
    print("Endpoint: POST / with JSON body {sessionID, question}")
    print("Health:   GET  /health")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    main()
