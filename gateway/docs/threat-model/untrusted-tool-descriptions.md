# Untrusted tool descriptions

## Threat

`tools/list` returns the tool description and the argument description. A model can read those strings as instructions. [count_words.py](../../src/gateway/tools/count_words.py) sets the tool description for `count_words`. The tool description is `WORD_COUNT_TOOL_DESCRIPTION`, `Count words by splitting on whitespace.` [text.py](../../src/gateway/tools/text.py) sets the `text` field description. That description is `TEXT_DESCRIPTION`, `Words are split on whitespace.` `tools/list` returns the string in either constant. The server lists the tool. The client chooses the tool. [First call](../../traces/first-call.md) records that choice.

## Measure

Treat the description as a label. A test fails when either string changes. [001. Orchestration](../adr/001-orchestration.md) records why the client sees the description. The orchestrator calls `tools/list`.

## Evaluation

Applied. [evals/tool_description_eval.py](../../evals/tool_description_eval.py) calls `tools/list` and compares each listed description with its constant. A failed line names the constant. Cursor runs that eval from [tool-description-eval.sh](../../../.cursor/hooks/tool-description-eval.sh) when an agent turn stops. On failure, the hook says that the eval failed and does not send the listed string.

## Server change

[count_words.py](../../src/gateway/tools/count_words.py) names `WORD_COUNT_TOOL_DESCRIPTION`, `WORD_COUNT_DESCRIPTION`, and `COUNT_DESCRIPTION`. [text.py](../../src/gateway/tools/text.py) names `TEXT_DESCRIPTION`. [server.py](../../src/gateway/server.py) passes `WORD_COUNT_TOOL_DESCRIPTION` to `mcp.tool()`. `count_words.__doc__` is that same string. The `text` field uses `TEXT_DESCRIPTION`. [tests/test_tools.py](../../tests/test_tools.py) compares `tools/list` and `count_words.__doc__` with those constants.
