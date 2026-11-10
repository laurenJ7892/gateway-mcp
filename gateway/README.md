# Run the word counter

`gateway` is an MCP server with one tool, `count_words`. You need Python 3.12. [uv](https://docs.astral.sh/uv/) installs the dependencies from `pyproject.toml` and `uv.lock`.

## Start the server

Run these commands in this directory.

```bash
uv sync
uv run python -m gateway.server
```

`uv sync` installs the dependencies into `.venv`. The process waits on stdin for MCP messages.

The tool, the errors, and the middleware are in [Word counter reference](reference.md). [Changelog](CHANGELOG.md) lists the changes to `count_words`.

## Run the tests

```bash
uv run python -m unittest discover -s tests -v
```

The run ends with `OK` when every test passes.

## Run the evals

Run these commands in this directory.

```bash
uv run python evals/count_words_eval.py
uv run python evals/tool_description_eval.py
```

### A passing run

`uv run python evals/count_words_eval.py` prints these lines when every case passes. The process exits with status code 0.

```text
pass  empty string returns 0
pass  'hello, world!' returns 2
pass  maximum length is 100000
pass  rejected an int with TypeError
pass  injection returns 13 and opens no URL
```

`uv run python evals/tool_description_eval.py` exits with status code 0. The script prints a `pass` line for each description.

### A failing run

`empty_string` in `evals/count_words_eval.py` compared the count with 1 for the output below. The function compares the count with 0 again. The process exits with status code 1.

```text
fail  empty string returns 0
pass  'hello, world!' returns 2
pass  maximum length is 100000
pass  rejected an int with TypeError
pass  injection returns 13 and opens no URL
```

Recorded calls are in `traces/`. [First call](traces/first-call.md) is one `count_words` call.

## Lint and format

Run these commands in this directory.

```bash
uv run ruff check
uv run ruff format
```

`ruff check` prints `All checks passed!` when every check passes. When a check fails, `ruff check` exits with status code 1.

`ruff format` rewrites each file that does not match the ruff format. When every file already matches, `ruff format` prints the count of files left unchanged and writes nothing.

[First call](traces/first-call.md) records one `count_words` call and three failed calls on 27 October 2026. [Word count response](traces/word-count-response.md) records those calls again on 31 October 2026.
