# Summary

Each file in this folder names one threat, one measure, one evaluation, and one server change. [template.md](template.md) sets that shape. This file records the measure, the evaluation, and the commit that adopts the measure. `Commit` is the subject line. `Date` is the commit date, written `YYYY-MM-DD`. `Commit` and `Date` stay empty until that commit exists. An ADR link belongs in the threat file.

## Untrusted tool descriptions

[Untrusted tool descriptions](untrusted-tool-descriptions.md)

Threat: `tools/list` returns the tool description and the argument description. A model can read those strings as instructions.

Measure: Treat the description as a label. A test fails when either string changes.

Evaluation: Not applied yet. No test fails when either description string changes.

Commit:

Date:

## Secrets in config

[Secrets in config](secrets-in-config.md)

Threat: A token in a config file, the process environment, or a log line can leave the process.

Measure: The logger writes no secret. `content` and `structured_content` hold no secret.

Evaluation: Applied for the config file, the environment, and the log line. A rejected argument can still appear in the tool error.

Commit:

Date:

## A tool result that tries to redirect the agent

[A tool result that tries to redirect the agent](tool-result-redirect.md)

Threat: A client that reads `content` as the next instruction can follow a tool result.

Measure: Return a `WordCount`. `content` and `structured_content` include no `text`.

Evaluation: Applied. [tests/test_tools.py](../../tests/test_tools.py) has no `Client.call_tool` test of `content` yet.

Commit:

Date:

## A tool that could write or delete

[A tool that could write or delete](write-or-delete.md)

Threat: A tool that writes a file or deletes a file changes the machine.

Measure: The server registers `count_words` only. `tools/list` reports `readOnlyHint` true, `destructiveHint` false, and `openWorldHint` false.

Evaluation: Applied for the registered tool. The read-only hints are not applied yet.

Commit:

Date:

## A missing human approval

[A missing human approval](missing-human-approval.md)

Threat: A registered tool that writes, deletes, or sends `text` would run through `tools/call` with no approval step.

Measure: Require approval for every registered tool except `count_words`. An unknown name still ends as `Unknown tool: phone_home`.

Evaluation: Not applied yet. The middleware list has no approval check.

Commit:

Date:
