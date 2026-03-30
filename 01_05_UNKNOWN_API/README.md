# 01_04_image_recognition (Python)

Vision-based image classification using native filesystem tools and the OpenAI **Responses API** (same flow as the former JS + MCP version).

## Run

```powershell
cd s01e04
$env:AI_API_KEY = "sk-..."   # or OPENAI_API_KEY
python app.py
```

No `pip install` is required (stdlib only). Optional: copy `env.example` to `.env` and set variables manually in the shell (this project does not auto-load `.env`).

## Setup

1. Set `AI_API_KEY` or `OPENAI_API_KEY` to a key that can call the Responses API.
2. Put source images in `images/`.
3. Keep character profiles in `knowledge/` (`*.md`).

## What it does

1. Reads profiles from `knowledge/` (`fs_list`, `fs_read`).
2. Inspects each file in `images/` with `understand_image` (vision).
3. Copies matches into `images/organized/<category>/` via `fs_copy`.

## Tools (replacing MCP)

| Tool              | Role                                      |
|-------------------|-------------------------------------------|
| `fs_list`         | List names in a folder                    |
| `fs_read`         | Read a text file                          |
| `fs_copy`         | Copy a file (creates parent dirs)         |
| `understand_image`| Vision Q&A on an image                    |

Paths are relative to the `s01e04` project root and cannot escape it.

## Optional env

- `OPENAI_MODEL` / `OPENAI_VISION_MODEL` — defaults to `gpt-4.1`
- `RESPONSES_API_ENDPOINT` — default OpenAI Responses URL
- `MAX_OUTPUT_TOKENS` — default `16384`
- `EXTRA_API_HEADERS` — JSON object for extra headers (e.g. proxies)
