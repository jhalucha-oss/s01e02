findhim_tools = [
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
        "name": "find_person_near_power_plant",
        "description": (
            "Analyze the provided suspects and the provided power plants, fetch "
            "sighting locations for each suspect, and use the Python distance "
            "function to find the person seen closest to a power plant. Call "
            "get_power_plants first, then pass its powerPlants result here."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "suspects": {
                    "type": "array",
                    "description": (
                        "List of suspects provided in the conversation. Each item "
                        "must include name, surname, and birthYear."
                    ),
                    "items": {
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
                            "birthYear": {
                                "type": "integer",
                                "description": "Birth year of the suspect",
                            },
                        },
                        "required": ["name", "surname", "birthYear"],
                        "additionalProperties": False,
                    },
                },
                "powerPlants": {
                    "type": "array",
                    "description": (
                        "Power plant data returned by get_power_plants. Each item "
                        "must include the plant name, coordinates, and code."
                    ),
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Power plant or city name",
                            },
                            "lat": {
                                "type": "number",
                                "description": "Latitude of the power plant",
                            },
                            "lon": {
                                "type": "number",
                                "description": "Longitude of the power plant",
                            },
                            "code": {
                                "type": "string",
                                "description": "Power plant code like PWR0000PL",
                            },
                        },
                        "required": ["name", "lat", "lon", "code"],
                        "additionalProperties": False,
                    },
                },
            },
            "required": ["suspects", "powerPlants"],
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
    },
]