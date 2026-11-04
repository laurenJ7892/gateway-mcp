# A missing human approval

## Threat

The client calls `tools/call` for `count_words` with no approval step. The call returns a count. If this server registered a tool that writes, deletes, or sends `text`, `tools/call` would run that tool with no approval step.

## Measure

Require approval for every registered tool except `count_words`. `count_words` runs with no approval. Any other registered tool waits until a person approves the call. An unknown name still ends as the tool error `Unknown tool: phone_home`. [First call](../../traces/first-call.md) records that error. [001. Orchestration](../adr/001-orchestration.md) chooses the option with fewer steps, so `count_words` has no approval step. A later choice that changes how approval works belongs in a new ADR.

## Evaluation

Not applied yet. [server.py](../../src/gateway/server.py) lists `TimingLog` and `MaxConcurrentCalls`. The middleware list has no approval check. An unknown name still ends as `Unknown tool: phone_home`. The server returns that text when the tool name is missing.

## Server change

Add `ApprovalGate` in [middleware.py](../../src/gateway/middleware.py). List `ApprovalGate` after `MaxConcurrentCalls` in [server.py](../../src/gateway/server.py). Give the gate two sets. One set holds the tools that run with no approval. The other set holds the registered tools. Both sets start as `count_words`. On `tools/call`, `count_words` proceeds to the next handler. A registered name absent from the no-approval set raises `MCPError` with code `-32000`. `needs_approval` in [errors.py](../../src/gateway/errors.py) returns `{name} needs human approval.` Any other name proceeds to the next handler. The server still returns `Unknown tool: phone_home` for that name.

Build the gate in a test with registered names `count_words` and `delete_file`, and with `count_words` in the no-approval set. The `delete_file` call raises. When `count_words` is the only registered name, the `phone_home` call proceeds to the next handler.
