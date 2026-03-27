import json
import os


AG3NTS_API_KEY = os.getenv("AG3NTS_API_KEY", "")


def _load_extra_headers() -> dict[str, str]:
    raw = os.getenv("EXTRA_API_HEADERS", "").strip()
    if not raw:
        return {}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise RuntimeError("EXTRA_API_HEADERS must be valid JSON") from error

    if not isinstance(parsed, dict):
        raise RuntimeError("EXTRA_API_HEADERS must decode to an object")

    return {str(key): str(value) for key, value in parsed.items()}


api = {
    "model": os.getenv("OPENAI_MODEL", "gpt-4.1"),
    "instructions": (
        "You are a helpful assistant with access to task-specific tools.\n"
        "You do not have file access. The suspect list is provided in the "
        "conversation.\n"
        "First call get_power_plants. Then call get_person_locations for given suspect."
        "Make each calculation using the calculate_distance_between_points function. "
        "After that retrieve the access level and send the final answer to "
        "verify.\n"
        "Be concise in your responses."
    ),
    "api_key": os.getenv("AI_API_KEY", ""),
    "ag3nts_api_key": os.getenv("AG3NTS_API_KEY", "8b965762-8a26-4ce5-aaa4-ec6dc43232c3"),
    "responses_api_endpoint": os.getenv(
        "RESPONSES_API_ENDPOINT",
        "https://api.openai.com/v1/responses",
    ),
    "location_api_endpoint": os.getenv(
        "LOCATION_API_ENDPOINT",
        "https://hub.ag3nts.org/api/location",
    ),
    "access_level_api_endpoint": os.getenv(
        "ACCESS_LEVEL_API_ENDPOINT",
        "https://hub.ag3nts.org/api/accesslevel",
    ),
    "verify_api_endpoint": os.getenv(
        "VERIFY_API_ENDPOINT",
        "https://hub.ag3nts.org/verify",
    ),
    "power_plants_url": os.getenv("POWER_PLANTS_URL", ""),
    "extra_headers": _load_extra_headers(),
}
