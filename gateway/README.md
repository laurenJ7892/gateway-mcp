# Run the word counter

`gateway` is an MCP server with one tool, `count_words`. You need Python 3.12. [uv](https://docs.astral.sh/uv/) installs the dependencies from `pyproject.toml` and `uv.lock`.

## Start the server

Run these commands in this directory.

```bash
uv sync
uv run python -m gateway.server
```

`uv sync` installs the dependencies into `.venv`. The process waits on stdin for MCP messages.

The tool, the errors, and the middleware are in [Word counter reference](reference.md).

## Run the tests

```bash
uv run python -m unittest discover -s tests -v
```

The run ends with `OK` when every test passes.

## Lint and format

Run these commands in this directory.

```bash
uv run ruff check
uv run ruff format
```

`ruff check` prints `All checks passed!` when every check passes. When a check fails, `ruff check` exits with status code 1.

`ruff format` rewrites each file that does not match the ruff format. When every file already matches, `ruff format` prints the count of files left unchanged and writes nothing.

[First call](traces/first-call.md) records one `count_words` call and three failed calls.
