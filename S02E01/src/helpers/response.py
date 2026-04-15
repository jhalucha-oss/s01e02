def extract_response_text(data: dict) -> str:
    ot = data.get("output_text")
    if isinstance(ot, str) and ot.strip():
        return ot

    messages = [
        item for item in (data.get("output") or []) if item.get("type") == "message"
    ]
    for message in messages:
        for part in message.get("content") or []:
            if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                return part["text"]
    return ""
