# 001. Orchestration

Status: accepted

Date: 2026-11-02

## Context

The orchestrator has to count words. One option calls `count_words` over MCP. The other option sends the text to a specialist over A2A. This record chooses the option with fewer steps.

This repo's word counter is the MCP server. The [Word counter reference](../../reference.md) describes that server. This repo has no A2A server. The A2A facts below come from the [A2A specification](https://a2a-protocol.org/latest/specification/).

A specialist can call MCP tools and hide those calls. Appendix B of the A2A specification says the specialist may use MCP. The orchestrator that sends the A2A message does not see those `tools/call` messages.

## Options

### The orchestrator calls MCP tools

The orchestrator is the MCP client. The orchestrator chooses the tool. This server uses MCP 2026-07-28. The [Tools page in the 2026-07-28 MCP specification](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) defines `tools/list` and `tools/call`.

The orchestrator calls `tools/list`, then `tools/call` with a tool name and arguments.

`tools/list` returns each tool's name, description, and argument schema. The [Word counter reference](../../reference.md) shows that schema for `count_words`. `output_schema` on the tool is the `WordCount` schema.

`tools/call` returns `content`, `structured_content`, and `is_error`. `count_words` sets `structured_content` to a `WordCount`. `count` is an integer with a minimum of 0.

`TimingLog` writes one line to the `gateway.middleware` logger. The line names the tool and the elapsed milliseconds.

MCP does not send the function body. In this repo that body is `count_words` in [server.py](../../src/gateway/server.py). A remote MCP server does not send its source either. The orchestrator still sees every tool call.

The server rejects arguments that fail the schema. `count_words` does not run for those arguments. A tool can set `is_error` to true. `MaxConcurrentCalls(4)` rejects a fifth `tools/call` with JSON-RPC code `-32000` and the message `Too many calls are already running. The limit is 4.`

#### Benefits

The orchestrator sends the name `count_words` and the arguments. The result is a `WordCount`. [Word count response](../../traces/word-count-response.md) stores one such call, including `{"text": "one two three"}` and `structured_content` of `{"count": 3}`.

#### Tradeoffs

The orchestrator has to know each tool. Each extra step is another `tools/call`. The orchestrator chooses the order of those calls. A new tool gives the orchestrator a new argument schema. The orchestrator sends the text in the `text` argument. The message contains the text. MCP still does not send a remote server's function body. An orchestrator that still reads `result` breaks when the result becomes `WordCount`. The [Changelog](../../CHANGELOG.md) records that change. [First call](../../traces/first-call.md) stores the earlier result, `{"result": 3}`.

#### When this option fits

Choose this option when the orchestrator has to say which tool ran, which arguments it sent, and what came back. Counting words is one tool the orchestrator already names. `MaxConcurrentCalls(4)` and `TimingLog` apply to that same call. This team can read `count_words` in this repo.

### A specialist over A2A

The [A2A specification](https://a2a-protocol.org/latest/specification/) uses the name opaque execution for agents that do not share internal state, memory, tools, thoughts, or plans.

The specialist can call MCP tools to do the work. Those calls are not A2A messages. The orchestrator does not see those calls unless the specialist copies them into a message or an artifact.

The orchestrator reads the agent card, then sends a message. The message has a `role` and one or more parts. A part is text, raw bytes, a URL, or structured data. The message can start a task.

The agent card includes `name`, `description`, `version`, `skills`, an endpoint, and authentication requirements. The orchestrator also sees the task id, the context id, the task state, later messages, and artifacts. The specialist puts results in artifacts. A message carries the conversation, a request for more input, or a status update. The specialist publishes the card at `/.well-known/agent-card.json`. The card does not include implementation details.

The orchestrator does not see the specialist's prompts, plans, memory, or tool calls. The specification defines no field for those.

The orchestrator sees a failed task as one of these states:

- `TASK_STATE_FAILED`
- `TASK_STATE_REJECTED`
- `TASK_STATE_CANCELED`

The task can also stop at `TASK_STATE_INPUT_REQUIRED` or `TASK_STATE_AUTH_REQUIRED`. A tool error inside the specialist stays inside the specialist unless the specialist copies that error into a message or an artifact. JSON-RPC `-32603` means an internal error on the specialist. That code does not name the tool.

The remaining states are `TASK_STATE_SUBMITTED`, `TASK_STATE_WORKING`, and `TASK_STATE_COMPLETED`.

#### Benefits

The orchestrator sends one message and receives an artifact. The specialist chooses the steps. The specialist can change prompts and tools without a new schema for the orchestrator. The orchestrator depends on the agent card and the task. The specialist keeps its state, memory, and tools. A long task can stop in `TASK_STATE_INPUT_REQUIRED` or `TASK_STATE_AUTH_REQUIRED` and continue as the same task.

#### Tradeoffs

The orchestrator cannot match an artifact to a tool call unless the specialist copies that call into a message or an artifact. `TASK_STATE_FAILED` does not name a tool. `-32603` does not name a tool either. The orchestrator trusts the specialist to choose the work. The agent card lists skills and does not list tools. This repo has no recorded A2A call. The orchestrator sees the text only if the specialist repeats it.

#### When this option fits

This option fits in any of these cases:

- The work stays one skill, and the orchestrator does not split that skill into tool calls.
- The specialist's prompts, tools, or data stay hidden from the orchestrator.
- Another team changes the tools and does not send this orchestrator a new argument schema.
- The orchestrator receives one task and one artifact. The error the orchestrator can see is a task state.

## Decision

This record chooses the orchestrator that calls MCP tools. That operation has fewer steps. The orchestrator calls `tools/list` and then `count_words`. The result is a `WordCount`. One process handles the call. The call has no agent card, no task, and no specialist.

A2A adds steps that counting words does not use. The orchestrator would read an agent card, send a message, follow the task state, and read an artifact. The specialist could then call tools the orchestrator does not see. This repo has no A2A server.

Revalidate this choice when one of these is true:

- The orchestrator has to order many `tools/call` messages.
- The prompts, the data, or the tool body have to stay hidden from the orchestrator.
- Another team owns the tool and changes it without a new schema for this orchestrator.
- The orchestrator needs one artifact, and the error the orchestrator can see is a task state.
- A specialist receives the work and calls these MCP tools itself. The orchestrator then does not see the `tools/call` messages.

## Consequences

The word counter stays an MCP server. This record does not change the server, the tests, or the traces. The orchestrator keeps the tool name, the arguments, and the `WordCount`. [Word count response](../../traces/word-count-response.md) is a stored call of that form.
