import json
from urllib import error, request

import src.S01E02Data as _data
from src.MathFunctions import haversine_distance
from src.config import api

_SUSPECTS = [
    {
        "name": person["name"],
        "surname": person["surname"],
        "birthYear": person.get("born", person.get("birthYear")),
    }
    for person in _data.people
]

def _post_json(url: str, payload: dict):
    headers = {
        "Content-Type": "application/json",
        **api.get("extra_headers", {}),
    }

    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as http_error:
        raw_body = http_error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError:
            parsed = {"error": {"message": raw_body or str(http_error)}}

        message = parsed.get("error", {}).get(
            "message",
            f"Request failed with status {http_error.code}",
        )
        raise RuntimeError(message) from http_error
    except error.URLError as url_error:
        raise RuntimeError(f"Request failed: {url_error.reason}") from url_error


def _require_api_value(key: str) -> str:
    value = api.get(key, "")
    if not value:
        raise RuntimeError(f"Missing required config value: {key}")
    return value


def _build_power_plants_url() -> str:
    configured_url = api.get("power_plants_url", "")
    if configured_url:
        return configured_url

    ag3nts_api_key = _require_api_value("ag3nts_api_key")
    return f"https://hub.ag3nts.org/data/{ag3nts_api_key}/findhim_locations.json"


def _get_json(url: str):
    headers = {
        **api.get("extra_headers", {}),
    }

    req = request.Request(
        url,
        headers=headers,
        method="GET",
    )

    try:
        with request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as http_error:
        raw_body = http_error.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw_body)
        except json.JSONDecodeError:
            parsed = {"error": {"message": raw_body or str(http_error)}}

        message = parsed.get("error", {}).get(
            "message",
            f"Request failed with status {http_error.code}",
        )
        raise RuntimeError(message) from http_error
    except error.URLError as url_error:
        raise RuntimeError(f"Request failed: {url_error.reason}") from url_error


_CITY_COORDS: dict[str, tuple[float, float]] = {
    "Zabrze": (50.3249, 18.7857),
    "Piotrków Trybunalski": (51.4047, 19.7030),
    "Grudziądz": (53.4840, 18.7534),
    "Tczew": (53.7764, 18.7753),
    "Radom": (51.4027, 21.1471),
    "Chelmno": (53.3493, 18.4238),
    "Chełmno": (53.3493, 18.4238),
    "Żarnowiec": (54.6167, 18.1167),
}


def _normalize_power_plants(data):
    # unwrap top-level envelope keys
    if isinstance(data, dict):
        if "powerPlants" in data:
            data = data["powerPlants"]
        elif "plants" in data:
            data = data["plants"]
        elif "power_plants" in data:
            data = data["power_plants"]

    # API returns {city_name: {code, is_active, power, ...}, ...}
    if isinstance(data, dict):
        items = []
        for city_name, details in data.items():
            if not isinstance(details, dict):
                continue
            code = details.get("code", details.get("plantCode"))
            lat_lon = _CITY_COORDS.get(city_name)
            items.append(
                {
                    "name": city_name,
                    "lat": lat_lon[0] if lat_lon else None,
                    "lon": lat_lon[1] if lat_lon else None,
                    "code": code,
                }
            )
        data = items

    if not isinstance(data, list):
        raise RuntimeError("Power plants source did not return a list")

    normalized = []

    for item in data:
        if not isinstance(item, dict):
            raise RuntimeError(f"Unsupported power plant format: {item}")

        name = item.get("name", item.get("city", item.get("location")))
        lat = item.get("lat", item.get("latitude"))
        lon = item.get("lon", item.get("lng", item.get("longitude")))
        code = item.get("code", item.get("plantCode", item.get("powerPlant")))

        if lat is None or lon is None:
            lat_lon = _CITY_COORDS.get(name) if name else None
            if lat_lon:
                lat, lon = lat_lon

        if name is None or code is None:
            raise RuntimeError(f"Missing power plant fields in item: {item}")

        if lat is None or lon is None:
            raise RuntimeError(
                f"No coordinates for power plant '{name}'. "
                f"Add it to _CITY_COORDS in handlers.py"
            )

        normalized.append(
            {
                "name": str(name),
                "lat": float(lat),
                "lon": float(lon),
                "code": str(code),
            }
        )

    return normalized


def _normalize_locations(data):
    if isinstance(data, dict):
        if "locations" in data:
            data = data["locations"]
        elif "data" in data:
            data = data["data"]

    if not isinstance(data, list):
        raise RuntimeError("Location API did not return a list of coordinates")

    normalized = []

    for item in data:
        if isinstance(item, dict):
            lat = item.get("lat", item.get("latitude"))
            lon = item.get("lon", item.get("lng", item.get("longitude")))
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            lat, lon = item
        else:
            raise RuntimeError(f"Unsupported location format: {item}")

        if lat is None or lon is None:
            raise RuntimeError(f"Missing coordinates in location item: {item}")

        normalized.append(
            {
                "lat": float(lat),
                "lon": float(lon),
            }
        )

    return normalized


def _normalize_birth_year(value):
    if isinstance(value, int):
        return value

    if isinstance(value, str):
        value = value.strip()
        if not value:
            raise RuntimeError("Birth year value is empty")

        if value.isdigit():
            return int(value)

        if len(value) >= 4 and value[:4].isdigit():
            return int(value[:4])

    raise RuntimeError(f"Unsupported birth year value: {value}")


def calculate_distance_between_points(args):
    distance_km = haversine_distance(
        args["person_latitude"],
        args["person_longitude"],
        args["power_plant_latitude"],
        args["power_plant_longitude"],
    )
    return {"distanceKm": round(distance_km, 3)}


def get_next_suspect(args):
    index = args.get("index", 0)

    if index < 0 or index >= len(_SUSPECTS):
        return {
            "suspect": None,
            "index": index,
            "total": len(_SUSPECTS),
            "hasMore": False,
        }

    suspect = _SUSPECTS[index]

    return {
        "suspect": suspect,
        "index": index,
        "total": len(_SUSPECTS),
        "hasMore": index + 1 < len(_SUSPECTS),
        "nextIndex": index + 1,
    }


def get_power_plants(args):
    response = _get_json(_build_power_plants_url())
    power_plants = _normalize_power_plants(response)

    return {
        "powerPlants": power_plants,
        "count": len(power_plants),
    }


def get_person_locations(args):
    payload = {
        "apikey": _require_api_value("ag3nts_api_key"),
        "name": args["name"],
        "surname": args["surname"],
    }

    response = _post_json(_require_api_value("location_api_endpoint"), payload)
    locations = _normalize_locations(response)

    return {
        "name": args["name"],
        "surname": args["surname"],
        "locations": locations,
    }


def get_access_level(args):
    payload = {
        "apikey": _require_api_value("ag3nts_api_key"),
        "name": args["name"],
        "surname": args["surname"],
        "birthYear": _normalize_birth_year(args["birthYear"]),
    }

    response = _post_json(_require_api_value("access_level_api_endpoint"), payload)

    if isinstance(response, dict):
        access_level = response.get("accessLevel", response.get("access_level"))
    else:
        access_level = None

    if access_level is None or access_level == "":
        raise RuntimeError(f"Access level missing in API response: {response}")

    access_level = int(access_level)

    return {
        "name": args["name"],
        "surname": args["surname"],
        "birthYear": payload["birthYear"],
        "accessLevel": access_level,
    }


def send_verify(args):
    answer = {
        "name": args["name"],
        "surname": args["surname"],
        "accessLevel": args["accessLevel"],
        "powerPlant": args["powerPlant"],
    }

    payload = {
        "apikey": _require_api_value("ag3nts_api_key"),
        "task": "findhim",
        "answer": answer,
    }

    response = _post_json(_require_api_value("verify_api_endpoint"), payload)

    return {
        "success": True,
        "sentAnswer": answer,
        "verifyResponse": response,
    }


handlers_finding_suspect = {
    "get_next_suspect": get_next_suspect,
    "get_power_plants": get_power_plants,
    "get_person_locations": get_person_locations,
    "calculate_distance_between_points": calculate_distance_between_points,
    "get_access_level": get_access_level,
    "send_verify": send_verify,
}

