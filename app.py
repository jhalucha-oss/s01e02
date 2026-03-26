import json
import src.S01E02Data as data
from src.config import api
from src.executor import process_query
from src.tools import handlers, tools


CONFIG = {
    "model": api["model"],
    "tools": tools,
    "handlers": handlers,
    "instructions": api["instructions"],
}


SUSPECTS = [
    {
        "name": person["name"],
        "surname": person["surname"],
        "birthYear": person["born"],
    }
    for person in data.people
]


def build_query() -> str:
    if not SUSPECTS:
        raise RuntimeError("Fill SUSPECTS with data from S01E01 before running the app.")

    return (
        "Solve the 'findhim' task using the provided conversation data.\n"
        "The suspect list is provided below.\n"
        "First call get_power_plants. Then call find_person_near_power_plant with "
        "the suspect list and the returned powerPlants. After that call "
        "get_access_level and finally send_verify.\n"
        f"Suspects: {json.dumps(SUSPECTS, ensure_ascii=False)}"
    )


def main() -> None:
    process_query(build_query(), CONFIG)


if __name__ == "__main__":
    main()
