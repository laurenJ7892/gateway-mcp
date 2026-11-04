# Secrets in config

## Threat

A token in a config file, the process environment, or a log line can leave the process. This server has no config file. `count_words` reads no environment variable. `TimingLog` in [middleware.py](../../src/gateway/middleware.py) writes one line to the `gateway.middleware` logger. The line names the tool and the elapsed milliseconds. The client can still send a secret in `text`.

## Measure

The logger writes no secret. `content` and `structured_content` hold no secret. The log line names the tool and the elapsed time. [001. Orchestration](../adr/001-orchestration.md) records that the orchestrator sends `text` on the call. A secret in `text` is part of that call.

## Evaluation

Applied for the config file, the environment, and the log line. A rejected argument can still appear in the tool error. [First call](../../traces/first-call.md) records `input_value=4` in that error. [tests/test_tools.py](../../tests/test_tools.py) does not yet assert that the log line omits `sk-test-secret`.

## Server change

Add a test in [tests/test_tools.py](../../tests/test_tools.py). Call `tools/call` with `sk-test-secret` in the arguments. The `gateway.middleware` line for that call names the tool and the elapsed time. The line contains no `sk-test-secret`.
