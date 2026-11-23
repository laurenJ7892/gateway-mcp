# 002. Harness

Status: proposed

Date: 2026-11-23

## Context

The client has to count words by calling this gateway. [001. Orchestration](001-orchestration.md) chooses that client. The client calls `tools/list`, sends the tool list to a model, and sends the model's tool call through `tools/call`. `PinGate`, `ReadOnlyMode`, and `ApprovalGate` check the call before the tool runs. The client appends the result and stops when the model returns a final answer.

This record chooses the loop for that work. One option is a script the client runs by hand. The other option is a Pydantic AI agent. The table names what the script does and what Pydantic AI does for the same job. The Pydantic AI column follows the [Deferred tools](https://pydantic.dev/docs/ai/tools-toolsets/deferred-tools/) page.

| The script | Pydantic AI |
| --- | --- |
| The script stops after 4 rounds if the model has not returned a final answer. | `UsageLimits(request_limit=4)` counts each model request. The agent raises `UsageLimitExceeded` before request 5. |
| The script appends a gateway error as the tool result. It does not call that tool again. A read-only block, a pin mismatch, and `most_common_word needs human approval.` all use that same result. | `ToolFailed` returns the failure to the model and does not spend `retries`. The model then chooses the next step. `ModelRetry` returns its message and spends one retry. Use `ModelRetry` when the model can fix the arguments, as with a schema rejection. After the last retry, the run raises to the caller. `DeferredToolResults.calls` holds a value, a `ModelRetry`, or a `ToolFailed`. |
| `most_common_word` returns `most_common_word needs human approval.` The script appends that message and continues. The script does not wait for a person. `ApprovalGate` still refuses the call. | `ApprovalRequiredToolset` wraps the MCP tools. `requires_approval=True` or `raise ApprovalRequired` adds the call to `DeferredToolRequests.approvals` before the tool function runs. A `HandleDeferredToolCalls` handler in the client process returns `DeferredToolResults`. The same `agent.run` then continues. `True` or `ToolApproved(override_args=...)` approves the call. `False` or `ToolDenied` denies the call, and the model sees the denial. If the person is outside the client process, the run ends only when `DeferredToolRequests` is in `output_type`. The next `agent.run` gets a new `run_id`. Pass `message_history` or the stored `conversation`, and pass `deferred_tool_results`. Keep the same `conversation_id`. Client approval is not `ApprovalGate`. `ApprovalGate` still refuses `most_common_word`. |
| The script sends `tools/call` to the gateway and waits. | The tool raises `CallDeferred` when another process must return the result. The call lands in `DeferredToolRequests.calls`. The tool function does not build that result. The client writes the result later in `DeferredToolResults.calls`. |
| The script sends the tool name and the arguments the model chose. The script keeps the messages. | `RunContext` carries `deps` from `agent.run(deps=...)`. The tool reads `ctx.deps`. The model does not set `deps`. `result.conversation` stores `deferred_tool_requests`. The client cannot rebuild those requests from the messages alone. The client stores the conversation when the answer comes later. |

## Options

### A script run by hand

The script calls `tools/list` and builds the prompt from that list. It calls the model, and it sends one `tools/call` when the model names a tool. The script stops on a final answer or after 4 rounds. The first model is a stub. The stub calls `count_words` once, then returns `The text has N words.`

#### Benefits

The script is the whole loop. The 4-round stop, the appended error, and the choice not to wait for a person are in that one file. The gateway in this repo still checks the call. The stub calls `count_words` with no model weights and no network.

#### Tradeoffs

The script counts to 4 rounds. It does not raise `UsageLimitExceeded`. The script turns every gateway error into one tool result. It has no `retries` count, so it cannot mark a block as `ToolFailed` and a bad argument as `ModelRetry`. A person cannot approve `most_common_word` before `tools/call`. Any value the tool needs has to be an argument the model chose, because the script has no `deps`. The script keeps its messages in memory. It does not store a `conversation`, so a later answer has no `deferred_tool_requests` to continue from.

#### When this option fits

Choose this option for the first client. That client counts one sentence with `count_words` and prints `The text has 3 words.` for `one two three`.

### A Pydantic AI agent

The client builds an `Agent` with the gateway tools. `agent.run` makes the model calls. `UsageLimits` limits requests. `ApprovalRequiredToolset` marks each gateway tool that needs a person. A `HandleDeferredToolCalls` handler approves or denies the call in the client process. The tool raises `CallDeferred` when the gateway must return the result. A tool that needs the MCP client takes `RunContext`.

#### Benefits

`request_limit` replaces the 4-round stop. `ToolFailed` returns a read-only block, a pin mismatch, or the approval error, and `ToolFailed` does not spend `retries`. `ModelRetry` is for arguments the model can change. `ApprovalRequiredToolset` pauses before `tools/call`. The handler continues the same `agent.run`. If the person is outside the client process, the client starts a new run and keeps `conversation_id`. `ctx.deps` holds the MCP client. The model still sends only the tool name and the arguments.

#### Tradeoffs

Pydantic AI runs the loop, so the client repo depends on that library. The stub becomes a model class for the agent. Client approval does not replace `ApprovalGate`. A client that submits `message_history` can approve a call that the agent never issued. The follow-up `agent.run` needs a new `run_id`. Do not reuse the paused `run_id`. The run can end on a pending call only when `DeferredToolRequests` is in `output_type`.

#### When this option fits

Choose this option when any of these is true:

- The person is in the client process, and `HandleDeferredToolCalls` approves the gateway tool before `tools/call`.
- The person answers later, outside the client process. The client stores `result.conversation` and starts a new run with the same `conversation_id`.
- The tool raises `CallDeferred`, and the client fills `DeferredToolResults.calls`.
- The tool needs `deps` on `RunContext`, and the model must not set `deps`.
- The stop raises `UsageLimitExceeded`, or the limit counts tokens.
- A block is `ToolFailed`, and a fixable argument is `ModelRetry`.

## Decision

This record chooses the script for the first client. That client only has to print a word count, and the script shows each step. The client is a new repo. This gateway stays the MCP server from [001. Orchestration](001-orchestration.md). `ApprovalGate` stays the server check for `most_common_word`.

Add Pydantic AI in this order after that first script works:

1. `ToolFailed` for a read-only block, a pin mismatch, and `most_common_word needs human approval.` `ModelRetry` only when a new argument can succeed.
2. `ApprovalRequiredToolset` around the gateway tools, and `HandleDeferredToolCalls` when the person is in the client process.
3. `UsageLimits(request_limit=4)`.
4. `RunContext` `deps` for the MCP client.
5. Store `result.conversation` when the answer can arrive later.

Revalidate the script when the first of those five is required. A read-only block, a pin mismatch, or the approval error is useless if the model spends `retries` on it. A client approval is useless if `ApprovalGate` still refuses the call.

## Consequences

This record does not change the gateway server, the tests, or the traces. The client repo does not exist yet. The first script lists the tools, calls the stub, sends `count_words` through the gateway, and prints `The text has N words.` The script appends `most_common_word needs human approval.` to the messages. The table names the Pydantic AI behavior that script lacks. Client approval does not remove `ApprovalGate`.
