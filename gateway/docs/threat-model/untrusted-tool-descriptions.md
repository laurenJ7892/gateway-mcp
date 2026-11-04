# Untrusted tool descriptions

## Threat

`tools/list` returns the tool description and the argument description. A model can read those strings as instructions. [server.py](../../src/gateway/server.py) sets both strings for `count_words`. The tool description is `TOOL_DESCRIPTION`, `Count words by splitting on whitespace.` The `text` field description is `TEXT_DESCRIPTION`, `Text to count. Words are split on whitespace.` `tools/list` returns the string in either constant. The server lists the tool. The client chooses the tool. [First call](../../traces/first-call.md) records that choice.

## Measure

Treat the description as a label. A test fails when either string changes. [001. Orchestration](../adr/001-orchestration.md) records why the client sees the description. The orchestrator calls `tools/list`.

## Evaluation

Applied. [server.py](../../src/gateway/server.py) names `TOOL_DESCRIPTION`, `TEXT_DESCRIPTION`, `WORD_COUNT_DESCRIPTION`, and `COUNT_DESCRIPTION`. `@mcp.tool()` receives `TOOL_DESCRIPTION`. The `text` field uses `TEXT_DESCRIPTION`. `count_words.__doc__` is `TOOL_DESCRIPTION`. [evals/tool_description_eval.py](../../evals/tool_description_eval.py) calls `tools/list` and compares each listed description with its constant. A failed line names the constant. Cursor runs that eval from [tool-description-eval.sh](../../../.cursor/hooks/tool-description-eval.sh) when an agent turn stops. The hook reports that the eval failed. The hook does not send the listed string. [tests/test_tools.py](../../tests/test_tools.py) compares the same strings.

## Server change

[server.py](../../src/gateway/server.py) names both strings. `TOOL_DESCRIPTION` is the argument to `@mcp.tool()`. `TEXT_DESCRIPTION` is the description of `text`. [tests/test_tools.py](../../tests/test_tools.py) reads `description` and `input_schema` from `list_tools` and compares them with those names. [evals/tool_description_eval.py](../../evals/tool_description_eval.py) makes that same `tools/list` call. Cursor calls the eval from [tool-description-eval.sh](../../../.cursor/hooks/tool-description-eval.sh).
