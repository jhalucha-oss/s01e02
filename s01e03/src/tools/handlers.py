import json
from urllib import error, request

from src.config import api


def _post_json(url: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as http_error:
        raw = http_error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = {"error": raw}
        raise RuntimeError(parsed.get("error", str(http_error))) from http_error
    except error.URLError as url_error:
        raise RuntimeError(f"Request failed: {url_error.reason}") from url_error


def check_package(args: dict) -> dict:
    """Fetch current status and destination of a package."""
    package_id = args["packageId"]
    ag3nts_key = api.get("ag3nts_api_key", "")
    if not ag3nts_key:
        raise RuntimeError("Missing AG3NTS_API_KEY")

    result = _post_json(
        api["package_api_endpoint"],
        {"apikey": ag3nts_key, "action": "check", "packageid": package_id},
    )
    return result


def redirect_package(args: dict) -> dict:
    """Redirect a package to a new destination."""
    package_id = args["packageId"]
    destination = args["destination"]
    code = args.get("code", "")
    ag3nts_key = api.get("ag3nts_api_key", "")
    if not ag3nts_key:
        raise RuntimeError("Missing AG3NTS_API_KEY")

    result = _post_json(
        api["package_api_endpoint"],
        {
            "apikey": ag3nts_key,
            "action": "redirect",
            "packageid": package_id,
            "destination": destination,
            "code": code,
        },
    )
    return result


handlers_proxy = {
    "check_package": check_package,
    "redirect_package": redirect_package,
}
