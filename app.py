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
        "Solve the 'findhim' task step by step:\n"
        "1. Call get_power_plants to get the list of power plants.\n"
        "2. Call get_next_suspect with index=0 to get the first suspect.\n"
        "3. Call get_person_locations for that suspect to get their sighting coordinates.\n"
        "4. limit pairs of to two per person ordered by smalles difference in lattitude and longitude, call calculate_distance_between_points  for filtered pairs]\n"
        "5. If hasMore is true, call get_next_suspect with nextIndex and repeat steps 3-4.\n"
        "6. After all suspects are processed, pick the one with the smallest distance "
        "to any power plant.\n"
        "7. Call get_access_level for that person.\n"
        "8. Call send_verify with the final answer.\n"
        "8. Always use tools - not using one is signal to code that program should end.\n"
        f"Total suspects: {len(SUSPECTS)}"
    )


def main() -> None:
    process_query(build_query(), CONFIG)


if __name__ == "__main__":
    main()
