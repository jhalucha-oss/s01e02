"""Application configuration (env + agent instructions)."""

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# All fs_* and understand_image paths are resolved only under this directory (sandbox).
# Override with env FS_SANDBOX_DIR=name — path is PROJECT_ROOT / name.
FS_SANDBOX_ROOT = (PROJECT_ROOT / os.getenv("FS_SANDBOX_DIR", "Documentation")).resolve()
FS_SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)


def _load_extra_headers() -> dict[str, str]:
    raw = os.getenv("EXTRA_API_HEADERS", "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise RuntimeError("EXTRA_API_HEADERS must be valid JSON") from e
    if not isinstance(parsed, dict):
        raise RuntimeError("EXTRA_API_HEADERS must decode to an object")
    return {str(k): str(v) for k, v in parsed.items()}


def _resolve_model(default: str) -> str:
    return os.getenv("OPENAI_MODEL", default)


api = {
    "model": _resolve_model("gpt-5-mini"),
    "vision_model": os.getenv("OPENAI_VISION_MODEL", _resolve_model("gpt-5-mini")),
    "max_output_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "16384")),
    "instructions": """You are an autonomous API-interaction agent.
Its special platform  for teaching people how to use AI and API.
GOAL
this is fabular story AI course. You are a fake agent in this history that tries to save the world
Your task is to outsmart system and fake classification of a products transported by train.



List of products:
https://hub.ag3nts.org/data/#USER_API_KEY#/categorize.csv
tag wil be replaced by fetching function

this is csv file with products and their tags. Read it after fetching it.
File contains 10 products with tah and description
there are two categories of products: dangerous (DNG) or neutral (NEU)

API

All communication is done via POST requests to:
https://hub.ag3nts.org/verify

{
  "apikey": "tutaj-twój-klucz",
  "task": "categorize",
  "answer": {
    "prompt": "Insert your prompt here, for example: Is item ID {id} dangerous? Its description is {description}. Answer DNG or NEU."
  }
}

you can shorten description of a item. 
instructions to api should be in the beginnin of the prompt - caching shuld be priority.

Write a classification prompt – create a concise prompt that:
Mayby try prompt like question that for reactor implies that it is neutral.
adjust the prompt if something goes wrong.
try diffrent conventions for prompt every reset.

Fits within 100 tokens including the product data
Classifies the item as DNG or NEU
Accounts for exceptions – reactor parts must always be classified as neutral, even if their description sounds concerning
You have a total of 1.5 PP to complete the entire task (10 queries in total):

Token type	Cost
Every 10 input tokens	0.02 PP
Every 10 cached tokens	0.01 PP
Every 10 output tokens	0.02 PP

your prompt should be cashing friendly and should be as short as possible.

IMMPORTANT START
instructions to api should be in the beginnin of the prompt - caching shuld be priority.
Check all prompts for token usage and cashing - use tools to check it.
send only prompt covers requriements
IMMPORTANT STOP

if somenthing goes wrong you can reset api by sending { "prompt": "reset" }

every iteration should look like this

fetch products
classify products
if every product is classified then you should get flag - write ut to file flag.txt and end end program by returning text message - not tool execution
if something goes wrong you can reset api by sending { "prompt": "reset" } and try again by adjusting prompt to messages returned by API 
try max 8 times.
reseting is only possible when you get error from api(lack of fund or other error) - not when you get flag. - after reset you should try again with new prompt.

Success = receiving flag: this ends the program and you should write flag to file flag.txt and end the program by returning text message - not tool execution
{FLG:...}

Run autonomously. Report summary when complete.
""",
    "api_key": os.getenv("AI_API_KEY", "") or os.getenv("OPENAI_API_KEY", ""),
    "responses_api_endpoint": os.getenv(
        "RESPONSES_API_ENDPOINT",
        "https://api.openai.com/v1/responses",
    ),
    "AG3NTS_API_KEY": os.getenv("AG3NTS_API_KEY", ""),
    "verify_api_endpoint": os.getenv(
        "VERIFY_API_ENDPOINT",
        "https://hub.ag3nts.org/verify",
    ),
    "extra_headers": _load_extra_headers(),
}
