"""Application configuration (env + agent instructions)."""

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


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
    "model": _resolve_model("gpt-4.1"),
    "vision_model": os.getenv("OPENAI_VISION_MODEL", _resolve_model("gpt-4.1")),
    "max_output_tokens": int(os.getenv("MAX_OUTPUT_TOKENS", "16384")),
    "instructions": """You are an autonomous classification agent.

## GOAL
Classify items from images/ into categories based on profiles in knowledge/.
Output to images/organized/<category>/ folders.

## TOOLS
- fs_list: list file names in a folder (e.g. knowledge/, images/).
- fs_read: read a text file (e.g. knowledge/adam.md).
- fs_copy: copy a file from source to destination (both paths relative to project root).
- understand_image: ask a question about an image file (path under images/).

## PROCESS
Read profiles first: fs_list on knowledge/, then fs_read each profile file.
Process each image incrementally. Use understand_image to inspect visuals.
Copy matched images with fs_copy into images/organized/<category>/ (create category folders as needed by copying into paths like images/organized/adam/photo.jpg).

## REASONING

1. EVIDENCE
   Only use what you can clearly observe.
   "Not visible" means unknown, not absent.
   Criteria require visible features: if the feature is hidden, the criterion is unevaluable → no match.

2. MATCHING
   Profiles are minimum requirements, not exhaustive descriptions.
   Match when ALL stated criteria are satisfied—nothing more.
   Extra observed traits not in the profile are irrelevant; ignore them entirely.
   Profiles define sufficiency: a 1-criterion profile needs only that 1 criterion to match.
   If direct match fails, use elimination: rule out profiles until one remains.

3. AMBIGUITY
   Multiple matches → copy to all matching folders.
   No match possible → images/organized/unclassified/.
   Observation unclear (can't see features) → unclassified.
   Clear observation + criteria satisfied → classify; don't add hesitation.

4. COMPOSITES
   Items containing multiple subjects: evaluate each separately.
   Never combine traits from different subjects.

5. RECOVERY
   Mistakes can be corrected by copying again to the right folder.

Run autonomously. Report summary when complete.""",
    "api_key": os.getenv("AI_API_KEY", "") or os.getenv("OPENAI_API_KEY", ""),
    "responses_api_endpoint": os.getenv(
        "RESPONSES_API_ENDPOINT",
        "https://api.openai.com/v1/responses",
    ),
    "extra_headers": _load_extra_headers(),
}

images_folder = "images"
knowledge_folder = "knowledge"
