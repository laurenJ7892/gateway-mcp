# Word counter reference

The server registers two tools, `count_words` and `most_common_word`. `count_words` splits text on whitespace and returns a `WordCount`. `most_common_word` returns the most common word and how many times it appears. Empty text returns a count of 0 from both tools. The server uses the 2026-07-28 MCP protocol over stdio.

Start commands are in [Run the word counter](README.md).

`src/gateway/server.py` passes `[TimingLog(), PinGate, ReadOnlyMode, MaxConcurrentCalls(4), ApprovalGate]`. That list is outermost first. `count_words` has no approval step. `most_common_word` needs human approval. These classes are defined in `src/gateway/middleware.py`. `count_words` and `WordCount` are defined in `src/gateway/tools/count_words.py`. `most_common_word` and `MostCommonWord` are defined in `src/gateway/tools/most_common_word.py`. `MAX_TEXT_LENGTH` and the `text` description are defined in `src/gateway/tools/text.py`.

## Tool

`count_words` takes one required string, `text`.

```json
{
  "type": "object",
  "properties": {
    "text": {
      "description": "Words are split on whitespace.",
      "maxLength": 100000,
      "type": "string"
    }
  },
  "required": ["text"]
}
```

`count_words` returns a `WordCount`. `count` is an integer with a minimum of 0.

```json
{
  "description": "How many words the text contains.",
  "properties": {
    "count": {
      "description": "Words in the text, split on whitespace.",
      "minimum": 0,
      "title": "Count",
      "type": "integer"
    }
  },
  "required": ["count"],
  "title": "WordCount",
  "type": "object"
}
```

A call with `{"text": "one two three"}` returns `{"count": 3}` in `structured_content`. The `content` text is `{`, a newline, two spaces, `"count": 3`, a newline, and `}`. A call with empty text, or with text that is only whitespace, returns `{"count": 0}` in `structured_content`. The `content` text for that call has `0` where the call above has `3`. The server rejects a missing `text`, a `text` that is not a string, or a `text` longer than 100000 characters. `count_words` does not run for those arguments.

## Errors

The server returns a JSON-RPC error when 4 `tools/call` requests are already running. The JSON-RPC code is `-32000`. The message is `Too many calls are already running. The limit is 4.` `too_many_calls` in `src/gateway/errors.py` builds that message.

`most_common_word` returns a JSON-RPC error. The code is `-32005`. The message is `most_common_word needs human approval.` `needs_approval` in `src/gateway/errors.py` builds that message.

A tool marked as writing returns a JSON-RPC error. The code is `-32006`. The message is `{name} is blocked in read-only mode.` `writes_blocked` in `src/gateway/errors.py` builds that message. A `ReadOnlyMode` with no server returns `Read-only mode has no server.` with code `-32006`.

## Middleware

`TimingLog` writes one line to the `gateway.middleware` logger. The line names a tool call by the tool name. The line names any other message by its method. `TimingLog` prints the elapsed milliseconds to two decimal places. When `count_words` takes 0.48 milliseconds, `TimingLog` writes `count_words completed in 0.48ms`. If the call raises, `TimingLog` writes `failed`. `TimingLog` then re-raises the error.

`PinGate` checks each `tools/call` against `pins.json`. The pin is a hash of the tool name, the description, the input schema, the output schema, and the annotations. A change to `read_only_hint`, or a tool that loses its annotations, is a different hash. The call runs when that hash matches. A different hash returns `tool_definition_changed` with code `-32001`. A tool with no pin returns `tool_not_pinned` with code `-32002`. A pins file that is not valid JSON, or that is not an object, returns code `-32003`. A `PinGate` with no server returns `Pin gate has no server.` with code `-32004`. A name the server does not register proceeds to the next handler.

`ReadOnlyMode` follows `PinGate`. It checks `read_only_hint` before the tool runs. `count_words` and `most_common_word` set `read_only_hint` to true, `destructive_hint` to false, and `open_world_hint` to false. `idempotent_hint` stays unset. Those calls proceed. A tool with no annotation, or with `read_only_hint` not true, raises `{name} is blocked in read-only mode.` with code `-32006`. The tool function does not run. A `ReadOnlyMode` with no server returns `Read-only mode has no server.` with code `-32006`. An unknown name proceeds to the next handler. `tools/list` does not take this check.

`MaxConcurrentCalls(4)` counts `tools/call` requests that are still running. The server refuses the fifth call with code `-32000`. The middleware frees the slot when the call finishes. `tools/list` and other methods do not take a slot.

`ApprovalGate` follows `MaxConcurrentCalls`. `count_words` proceeds. `most_common_word` raises `most_common_word needs human approval.` with code `-32005`. An unknown name proceeds to the next handler. The server returns `Unknown tool: phone_home` for that name.

## Recorded calls

[First call](traces/first-call.md) records the 27 October 2026 run. In that record, `structured_content` is `{"result": 3}`. [Word count response](traces/word-count-response.md) records the same calls on 31 October 2026. In that record, `structured_content` is `{"count": 3}`. [Most common word response](traces/most-common-word-response.md) records a `most_common_word` call on 11 November 2026. In that record, `structured_content` is `{"word": "one", "count": 2}`.
