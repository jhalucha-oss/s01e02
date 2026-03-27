findhim_tools = [
    {
        "type": "function",
        "name": "get_next_suspect",
        "description": (
            "Return one suspect from the suspects list by index. "
            "Start with index 0, then use nextIndex from the response to get the next one. "
            "When hasMore is false, all suspects have been processed."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "index": {
                    "type": "integer",
                    "description": "Zero-based index of the suspect to retrieve. Start at 0.",
                },
            },
            "required": ["index"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_power_plants",
        "description": (
            "Fetch the list of power plants from the remote findhim_locations.json "
            "file and return plant names, coordinates, and plant codes."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_person_locations",
        "description": (
            "Fetch all known sighting coordinates for a specific suspect from the "
            "location API."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "First name of the suspect",
                },
                "surname": {
                    "type": "string",
                    "description": "Last name of the suspect",
                },
            },
            "required": ["name", "surname"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_access_level",
        "description": (
            "Fetch the access level for a specific person using name, surname, "
            "and birthYear."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "First name of the person",
                },
                "surname": {
                    "type": "string",
                    "description": "Last name of the person",
                },
                "birthYear": {
                    "type": "integer",
                    "description": "Birth year of the person",
                },
            },
            "required": ["name", "surname", "birthYear"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "calculate_distance_between_points",
        "description": (
            "Calculate the distance between two points on the Earth's surface (example: distance between person and power plant)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                    "person_latitude": {
                        "type": "number",
                        "description": "Latitude of the person",
                },
                "person_longitude": {
                        "type": "number",
                        "description": "Longitude of the person",
                },
                "power_plant_latitude": {
                    "type": "number",
                    "description": "Latitude of the power plant",
                },
                "power_plant_longitude": {
                    "type": "number",
                    "description": "Longitude of the power plant",
                },
            },
            "required": ["person_latitude", "person_longitude", "power_plant_latitude", "power_plant_longitude"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "send_verify",
        "description": (
            "Send the final answer for the findhim task to the verify endpoint."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "First name of the identified person",
                },
                "surname": {
                    "type": "string",
                    "description": "Last name of the identified person",
                },
                "accessLevel": {
                    "type": "integer",
                    "description": "Access level returned by the API",
                },
                "powerPlant": {
                    "type": "string",
                    "description": "Power plant code like PWR0000PL",
                },
            },
            "required": ["name", "surname", "accessLevel", "powerPlant"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]