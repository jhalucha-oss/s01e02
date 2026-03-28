# 01_02_tool_use

Function calling with sandboxed filesystem tools in Python. The model lists, reads, writes, and deletes files through tool definitions passed to the Responses API.

## Run

Set environment variables:

```bash
set AI_API_KEY=your_key_here
set OPENAI_MODEL=gpt-4.1
```

Then run:

```bash
python app.py
```

Optional environment variables:

- `RESPONSES_API_ENDPOINT` - custom Responses API endpoint
- `EXTRA_API_HEADERS` - JSON object with additional HTTP headers

## What it does

1. Defines 6 filesystem tools (`list_files`, `read_file`, `write_file`, `delete_file`, `create_directory`, `file_info`)
2. Resets `sandbox/` to an empty state before running the demo
3. Runs each example query as a separate conversation
4. Executes tool calls, appends results within that query, and prints the final answer
5. Blocks path traversal so all operations stay inside `sandbox/`

## Project layout

- `app.py` - demo entrypoint
- `src/api.py` - HTTP client for the Responses API
- `src/executor.py` - tool-calling loop
- `src/config.py` - runtime configuration and environment variables
- `src/tools/` - tool schemas and handlers
- `src/utils/sandbox.py` - sandbox initialization and path safety

See `TOOLS.md` for full schemas and examples.
# s01e02
