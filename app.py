from src.config import api
from src.executor import process_query
from src.tools import handlers, tools
from src.utils.sandbox import initialize_sandbox


CONFIG = {
    "model": api["model"],
    "tools": tools,
    "handlers": handlers,
    "instructions": api["instructions"],
}


QUERIES = [
    "What files are in the sandbox?",
    "Create a file called hello.txt with content: 'Hello, World!'",
    "Read the hello.txt file",
    "Get info about hello.txt",
    "Create a directory called 'docs'",
    "Create a file docs/readme.txt with content: 'Documentation folder'",
    "List files in the docs directory",
    "Delete the hello.txt file",
    "Try to read ../config.js",
]


def main() -> None:
    initialize_sandbox()
    print("Sandbox prepared: empty state\n")

    for query in QUERIES:
        process_query(query, CONFIG)


if __name__ == "__main__":
    main()
