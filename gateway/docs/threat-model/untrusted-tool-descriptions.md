# Untrusted tool descriptions

## Threat

`tools/list` returns the tool description and the argument description. A model can read those strings as instructions. [server.py](../../src/gateway/server.py) sets both strings for `count_words`. The tool description is the docstring `Count words by splitting on whitespace.` The `text` field description is `Text to count. Words are split on whitespace.` `tools/list` returns the string that sits in either place. The server lists the tool. The client chooses the tool. [First call](../../traces/first-call.md) records that choice.

## Measure

Treat the description as a label. A test fails when either string changes. [001. Orchestration](../adr/001-orchestration.md) records why the client sees the description. The orchestrator calls `tools/list`.

## Evaluation

Not applied yet. Both strings are still the docstring and the field description in [server.py](../../src/gateway/server.py). [tests/test_tools.py](../../tests/test_tools.py) has no check that fails when either string changes.

## Server change

Name both strings in [server.py](../../src/gateway/server.py). Pass the tool description to `@mcp.tool()`. Use the field description on the `text` field. [tests/test_tools.py](../../tests/test_tools.py) reads `description` and `input_schema` from `list_tools`. The test compares those values with the named strings.
