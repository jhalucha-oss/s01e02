proxy_tools = [
    {
        "type": "function",
        "name": "check_package",
        "description": (
            "Check the current status and destination of a package by its ID. "
            "Returns package details including description, current location, and destination."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "packageId": {
                    "type": "string",
                    "description": "The unique identifier of the package to check.",
                },
            },
            "required": ["packageId"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "redirect_package",
        "description": (
            "Change the destination of a package. "
            "Returns confirmation of the new destination."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "packageId": {
                    "type": "string",
                    "description": "The unique identifier of the package to redirect.",
                },
                "destination": {
                    "type": "string",
                    "description": "The new destination code, e.g. PWR6132PL.",
                },
                "code": {
                    "type": "string",
                    "description": "Security code required to authorize the redirection.",
                },
            },
            "required": ["packageId", "destination", "code"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]
