# A tool that could write or delete

## Threat

A tool that writes a file or deletes a file changes the machine. `count_words` splits a string and returns an integer. The function opens no file, no socket, and no URL. [tests/test_count_words.py](../../tests/test_count_words.py) requires the registered names to be `count_words` and `most_common_word`. `count_words` sets no `ToolAnnotations`. The SDK default for `read_only_hint` is false, so a missing hint describes a tool that can modify its environment. The SDK default for `open_world_hint` is true, so a missing hint describes a tool that can interact with external entities. The SDK documents every annotation as a hint. The SDK tells a client to ignore those hints when the server is untrusted.

## Measure

The server registers `count_words` and `most_common_word`. `count_words` returns a count. `most_common_word` returns a word and a count. `tools/list` reports `readOnlyHint` true, `destructiveHint` false, and `openWorldHint` false. [001. Orchestration](../adr/001-orchestration.md) records that the orchestrator calls `count_words` by name.

## Evaluation

Applied for the registered tools. The server registers `count_words` and `most_common_word`. [tests/test_count_words.py](../../tests/test_count_words.py) requires that set of names. `count_words` returns a count. The read-only hints are not applied yet. `count_words` sets no `ToolAnnotations`. `tools/list` omits `readOnlyHint`, `destructiveHint`, and `openWorldHint`.

## Server change

Pass `ToolAnnotations` to `@mcp.tool()` in [server.py](../../src/gateway/server.py). Set `read_only_hint` to true, `destructive_hint` to false, and `open_world_hint` to false. Leave `idempotent_hint` unset. The SDK reads `idempotent_hint` only when `read_only_hint` is false. [tests/test_count_words.py](../../tests/test_count_words.py) reads the three hints from `list_tools`.
