import asyncio
import unittest
from types import SimpleNamespace

from mcp import Client
from mcp.shared.exceptions import MCPError

from gateway.errors import too_many_calls
from gateway.middleware import MaxConcurrentCalls, TimingLog
from gateway.server import mcp
from gateway.tools.count_words import (
    COUNT_DESCRIPTION,
    WORD_COUNT_DESCRIPTION,
    WORD_COUNT_TOOL_DESCRIPTION,
    count_words,
)
from gateway.tools.text import MAX_TEXT_LENGTH, TEXT_DESCRIPTION


def _run(coro):
    return asyncio.run(coro)


def _count_text(count: int) -> str:
    return f'{{\n  "count": {count}\n}}'


class CountWordsTests(unittest.TestCase):
    def test_splits_on_whitespace(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "count_words", {"text": "  one\ttwo\nthree  "}
                )
            self.assertFalse(result.is_error)
            self.assertEqual(result.content[0].text, _count_text(3))
            return result.structured_content

        self.assertEqual(_run(call()), {"count": 3})

    def test_empty_text_is_zero(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool("count_words", {"text": "   \n"})
            self.assertFalse(result.is_error)
            self.assertEqual(result.content[0].text, _count_text(0))
            return result.structured_content

        self.assertEqual(_run(call()), {"count": 0})

    def test_text_at_the_maximum_is_counted(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "count_words", {"text": "a" * MAX_TEXT_LENGTH}
                )
            self.assertFalse(result.is_error)
            self.assertEqual(result.content[0].text, _count_text(1))
            return result.structured_content

        self.assertEqual(_run(call()), {"count": 1})

    def test_text_over_the_maximum_is_rejected(self) -> None:
        async def call() -> None:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "count_words", {"text": "a" * (MAX_TEXT_LENGTH + 1)}
                )
            self.assertTrue(result.is_error)
            self.assertIsNone(result.structured_content)
            self.assertIn(str(MAX_TEXT_LENGTH), result.content[0].text)

        _run(call())

    def test_listed_descriptions_match_the_constants(self) -> None:
        async def listed() -> tuple[str | None, str]:
            async with Client(mcp) as client:
                page = await client.list_tools()
            tool = next(tool for tool in page.tools if tool.name == "count_words")
            text = tool.input_schema["properties"]["text"]["description"]
            return tool.description, text

        self.assertEqual(
            _run(listed()), (WORD_COUNT_TOOL_DESCRIPTION, TEXT_DESCRIPTION)
        )
        self.assertEqual(count_words.__doc__, WORD_COUNT_TOOL_DESCRIPTION)

    def test_registered_tools(self) -> None:
        async def names() -> set[str]:
            async with Client(mcp) as client:
                page = await client.list_tools()
            return {tool.name for tool in page.tools}

        self.assertEqual(_run(names()), {"count_words", "most_common_word"})

    def test_output_schema_is_word_count(self) -> None:
        async def schema() -> dict:
            async with Client(mcp) as client:
                page = await client.list_tools()
            tool = next(tool for tool in page.tools if tool.name == "count_words")
            return tool.output_schema

        self.assertEqual(
            _run(schema()),
            {
                "description": WORD_COUNT_DESCRIPTION,
                "properties": {
                    "count": {
                        "description": COUNT_DESCRIPTION,
                        "minimum": 0,
                        "title": "Count",
                        "type": "integer",
                    }
                },
                "required": ["count"],
                "title": "WordCount",
                "type": "object",
            },
        )


def _call(method: str, name: str | None = None) -> SimpleNamespace:
    params = {"name": name} if name is not None else None
    return SimpleNamespace(method=method, params=params)


class MiddlewareTests(unittest.TestCase):
    def test_timing_log_names_the_tool(self) -> None:
        async def call_next(ctx: SimpleNamespace) -> dict[str, bool]:
            return {"ok": True}

        async def run() -> None:
            with self.assertLogs("gateway.middleware", level="INFO") as logged:
                result = await TimingLog()(
                    _call("tools/call", "count_words"), call_next
                )
            self.assertEqual(result, {"ok": True})
            self.assertIn("count_words completed", logged.output[0])
            self.assertIn("ms", logged.output[0])

        _run(run())

    def test_timing_log_records_a_failure(self) -> None:
        async def call_next(ctx: SimpleNamespace) -> None:
            raise RuntimeError("broken")

        async def run() -> None:
            with (
                self.assertLogs("gateway.middleware", level="INFO") as logged,
                self.assertRaises(RuntimeError),
            ):
                await TimingLog()(_call("tools/call", "count_words"), call_next)
            self.assertIn("count_words failed", logged.output[0])

        _run(run())

    def test_second_tool_call_is_refused(self) -> None:
        limit = MaxConcurrentCalls(1)
        started = asyncio.Event()
        release = asyncio.Event()

        async def call_next(ctx: SimpleNamespace) -> str:
            started.set()
            await release.wait()
            return "done"

        async def run() -> None:
            ctx = _call("tools/call", "count_words")
            first = asyncio.create_task(limit(ctx, call_next))
            await started.wait()
            with self.assertRaises(MCPError) as caught:
                await limit(ctx, call_next)
            self.assertEqual(str(caught.exception), too_many_calls(1))
            release.set()
            self.assertEqual(await first, "done")

        _run(run())

    def test_other_methods_do_not_use_a_slot(self) -> None:
        limit = MaxConcurrentCalls(1)
        started = asyncio.Event()
        release = asyncio.Event()

        async def busy(ctx: SimpleNamespace) -> str:
            started.set()
            await release.wait()
            return "done"

        async def listing(ctx: SimpleNamespace) -> str:
            return "listed"

        async def run() -> None:
            first = asyncio.create_task(limit(_call("tools/call", "count_words"), busy))
            await started.wait()
            self.assertEqual(await limit(_call("tools/list"), listing), "listed")
            release.set()
            self.assertEqual(await first, "done")

        _run(run())

    def test_slot_frees_after_the_call(self) -> None:
        limit = MaxConcurrentCalls(1)

        async def call_next(ctx: SimpleNamespace) -> str:
            return "done"

        async def run() -> None:
            ctx = _call("tools/call", "count_words")
            self.assertEqual(await limit(ctx, call_next), "done")
            self.assertEqual(await limit(ctx, call_next), "done")

        _run(run())


if __name__ == "__main__":
    unittest.main()
