# s01e03 – Proxy HTTP Server

HTTP proxy server that acts as a logistics assistant.  
Uses LLM function calling to handle package check/redirect requests.

## Setup

```
cd C:\ZRODLA\s01e03

# Copy .env from s01e02 or set variables manually
set AI_API_KEY=your_openai_key
set AG3NTS_API_KEY=your_ag3nts_key
```

## Run

```
python server.py
```

Server starts on `http://0.0.0.0:8000`

## API

**POST /**

```json
{
  "sessionID": "abc123",
  "question": "Gdzie jest paczka PKG001?"
}
```

Response:
```json
{
  "reply": "Paczka PKG001 jest obecnie w Warszawie..."
}
```

**GET /health** – health check

## Next steps

1. Start server: `python server.py`
2. Test locally: send POST to `http://localhost:8000`
3. Expose publicly with ngrok: `ngrok http 8000`
4. Submit URL to Hub `/verify` with task name `proxy`
