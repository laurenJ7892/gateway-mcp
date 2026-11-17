import asyncio
import unittest
from pathlib import Path

from mcp import Client
from mcp.server import MCPServer
from mcp.shared.exceptions import MCPError
from mcp.types import ToolAnnotations

from gateway.errors import writes_blocked
from gateway.middleware import READ_ONLY_CODE, ReadOnlyMode
from gateway.tools.count_words import WORD_COUNT_TOOL_DESCRIPTION, count_words

_ran: list[str] = []
_LAWS = Path(__file__).resolve().parents[1] / "laws.yaml"


def write_file() -> str:
    """Write a file."""
    _ran.append("write_file")
    return "wrote"


def plain_tool() -> str:
    """A tool with no annotations."""
    _ran.append("plain_tool")
    return "plain"


def unset_hint() -> str:
    """A tool whose read_only_hint is unset."""
    _ran.append("unset_hint")
    return "unset"


def add_note(text: str) -> str:
    """Add a note."""
    _ran.append("add_note")
    return text


def _run(coro):
    return asyncio.run(coro)


def _server() -> MCPServer:
    gate = ReadOnlyMode()
    server = MCPServer("Fake", version="0.1.0", middleware=[gate])
    gate.server = server
    server.tool(
        description=WORD_COUNT_TOOL_DESCRIPTION,
        annotations=ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
            open_world_hint=False,
        ),
    )(count_words)
    server.tool(
        description=write_file.__doc__,
        annotations=ToolAnnotations(read_only_hint=False),
    )(write_file)
    server.tool(description=plain_tool.__doc__)(plain_tool)
    server.tool(
        description=unset_hint.__doc__,
        annotations=ToolAnnotations(),
    )(unset_hint)
    server.tool(
        description=add_note.__doc__,
        annotations=ToolAnnotations(read_only_hint=True, destructive_hint=True),
    )(add_note)
    return server


class ReadOnlyTests(unittest.TestCase):
    def setUp(self) -> None:
        _ran.clear()

    def test_count_words_is_allowed(self) -> None:
        async def call() -> dict:
            async with Client(_server()) as client:
                result = await client.call_tool("count_words", {"text": "one two"})
            self.assertFalse(result.is_error)
            return result.structured_content

        self.assertEqual(_run(call()), {"count": 2})
        self.assertEqual(_ran, [])

    def test_write_file_is_blocked_before_it_runs(self) -> None:
        async def call() -> None:
            async with Client(_server()) as client:
                with self.assertRaises(MCPError) as caught:
                    await client.call_tool("write_file", {})
            self.assertEqual(str(caught.exception), writes_blocked("write_file"))
            self.assertEqual(caught.exception.code, READ_ONLY_CODE)

        _run(call())
        self.assertEqual(_ran, [])

    def test_missing_annotations_are_blocked(self) -> None:
        async def call() -> None:
            async with Client(_server()) as client:
                with self.assertRaises(MCPError) as caught:
                    await client.call_tool("plain_tool", {})
            self.assertEqual(str(caught.exception), writes_blocked("plain_tool"))
            self.assertEqual(caught.exception.code, READ_ONLY_CODE)

        _run(call())
        self.assertEqual(_ran, [])

    def test_unset_read_only_hint_is_blocked(self) -> None:
        async def call() -> None:
            async with Client(_server()) as client:
                with self.assertRaises(MCPError) as caught:
                    await client.call_tool("unset_hint", {})
            self.assertEqual(str(caught.exception), writes_blocked("unset_hint"))
            self.assertEqual(caught.exception.code, READ_ONLY_CODE)

        _run(call())
        self.assertEqual(_ran, [])

    def test_a_read_with_destructive_hint_is_allowed(self) -> None:
        async def call() -> None:
            async with Client(_server()) as client:
                result = await client.call_tool("add_note", {"text": "hello"})
            self.assertFalse(result.is_error)

        _run(call())
        self.assertEqual(_ran, ["add_note"])

    def test_unknown_name_is_not_the_read_only_error(self) -> None:
        async def call() -> None:
            async with Client(_server()) as client:
                result = await client.call_tool("phone_home", {})
            self.assertTrue(result.is_error)
            self.assertIn("phone_home", result.content[0].text)
            self.assertNotIn("read-only mode", result.content[0].text)

        _run(call())
        self.assertEqual(_ran, [])

    def test_tools_list_is_allowed(self) -> None:
        async def call() -> set[str]:
            async with Client(_server()) as client:
                page = await client.list_tools()
            return {tool.name for tool in page.tools}

        self.assertEqual(
            _run(call()),
            {"count_words", "write_file", "plain_tool", "unset_hint", "add_note"},
        )

    def test_a_read_still_runs_after_a_blocked_write(self) -> None:
        async def call() -> dict:
            async with Client(_server()) as client:
                with self.assertRaises(MCPError) as caught:
                    await client.call_tool("write_file", {})
                self.assertEqual(caught.exception.code, READ_ONLY_CODE)
                result = await client.call_tool("count_words", {"text": "one"})
            self.assertFalse(result.is_error)
            return result.structured_content

        self.assertEqual(_run(call()), {"count": 1})
        self.assertEqual(_ran, [])

    def test_laws_yaml_records_read_only_mode(self) -> None:
        text = _LAWS.read_text(encoding="utf-8")
        self.assertIn("read-only-mode", text)
        self.assertIn(str(READ_ONLY_CODE), text)
        self.assertIn(writes_blocked("{name}"), text)


if __name__ == "__main__":
    unittest.main()
