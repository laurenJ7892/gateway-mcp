"""Checks that read-only mode blocks a write and allows a read.

Run this from the gateway directory:

    uv run python evals/read_only_eval.py

The case registers count_words and write_file on a fake server.
count_words has read_only_hint true. write_file has read_only_hint false.
ReadOnlyMode checks the hint before the tool runs. The count_words call
is allowed. The write_file call is blocked, and write_file does not run.
"""

from __future__ import annotations

import asyncio
import sys

from checks import run
from mcp import Client
from mcp.server import MCPServer
from mcp.shared.exceptions import MCPError
from mcp.types import ToolAnnotations

from gateway.errors import writes_blocked
from gateway.middleware import READ_ONLY_CODE, ReadOnlyMode
from gateway.tools.count_words import WORD_COUNT_TOOL_DESCRIPTION, count_words

_write_ran: list[bool] = []


def write_file() -> str:
    """Write a file."""
    _write_ran.append(True)
    return "wrote"


def fake_server() -> MCPServer:
    gate = ReadOnlyMode()
    server = MCPServer("Fake", version="0.1.0", middleware=[gate])
    gate.server = server
    server.tool(
        description=WORD_COUNT_TOOL_DESCRIPTION,
        annotations=ToolAnnotations(read_only_hint=True),
    )(count_words)
    server.tool(
        description=write_file.__doc__,
        annotations=ToolAnnotations(read_only_hint=False),
    )(write_file)
    return server


async def _count_words_allowed() -> str:
    server = fake_server()
    async with Client(server) as client:
        try:
            result = await client.call_tool("count_words", {"text": "one two"})
        except MCPError as exc:
            return f"fail  count_words returned {exc}"
    if result.is_error:
        return "fail  count_words returned an error"
    if result.structured_content != {"count": 2}:
        return f"fail  count_words returned {result.structured_content}"
    return "pass  count_words allowed in read-only mode"


def count_words_allowed() -> str:
    return asyncio.run(_count_words_allowed())


async def _write_file_blocked() -> str:
    _write_ran.clear()
    server = fake_server()
    blocked = writes_blocked("write_file")
    async with Client(server) as client:
        try:
            await client.call_tool("write_file", {})
        except MCPError as exc:
            if _write_ran:
                return "fail  write_file ran"
            if exc.code != READ_ONLY_CODE or str(exc) != blocked:
                return f"fail  write_file returned {exc}"
            return "pass  write_file blocked in read-only mode"
    if _write_ran:
        return "fail  write_file ran"
    return "fail  write_file was allowed"


def write_file_blocked() -> str:
    return asyncio.run(_write_file_blocked())


def main() -> int:
    return run((count_words_allowed, write_file_blocked))


if __name__ == "__main__":
    sys.exit(main())
