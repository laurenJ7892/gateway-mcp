# Word counter reference

The server registers one tool, `count_words`. The tool splits text on whitespace and returns a `WordCount`. The server uses the 2026-07-28 MCP protocol over stdio.

Start commands are in [Run the word counter](README.md).

`src/gateway/server.py` passes `[TimingLog(), MaxConcurrentCalls(4)]`. That list is outermost first. Both classes are defined in `src/gateway/middleware.py`.

## Tool

`count_words` takes one required string, `text`.

```json
{
  "type": "object",
  "properties": {
    "text": {
      "description": "Text to count. Words are split on whitespace.",
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

## Middleware

`TimingLog` writes one line to the `gateway.middleware` logger. The line names a tool call by the tool name. The line names any other message by its method. `TimingLog` prints the elapsed milliseconds to two decimal places. When `count_words` takes 0.48 milliseconds, `TimingLog` writes `count_words completed in 0.48ms`. If the call raises, `TimingLog` writes `failed`. `TimingLog` then re-raises the error.

`MaxConcurrentCalls(4)` counts `tools/call` requests that are still running. The server refuses the fifth call with code `-32000`. The middleware frees the slot when the call finishes. `tools/list` and other methods do not take a slot.

## Recorded calls

[First call](traces/first-call.md) records the 27 October 2026 run. In that record, `structured_content` is `{"result": 3}`. [Word count response](traces/word-count-response.md) records the same calls on 31 October 2026. In that record, `structured_content` is `{"count": 3}`.
