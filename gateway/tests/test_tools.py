import asyncio
import unittest
from types import SimpleNamespace

from mcp import Client
from mcp.server.mcpserver.exceptions import ToolError
from mcp.shared.exceptions import MCPError

from gateway.errors import GatewayError, too_many_calls
from gateway.middleware import MaxConcurrentCalls, TimingLog
from gateway.server import WordData, mcp


def _run(coro):
    return asyncio.run(coro)


class CountWordsTests(unittest.TestCase):
    def test_splits_on_whitespace(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "count_words", {"text": "  one\ttwo\nthree  "}
                )
            self.assertFalse(result.is_error)
            return result.structured_content

        self.assertEqual(_run(call()), {"result": 3})

    def test_empty_text_is_zero(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool("count_words", {"text": "   \n"})
            return result.structured_content

        self.assertEqual(_run(call()), {"result": 0})

    def test_only_count_words_is_registered(self) -> None:
        async def names() -> set[str]:
            async with Client(mcp) as client:
                page = await client.list_tools()
            return {tool.name for tool in page.tools}

        self.assertEqual(_run(names()), {"count_words"})


class WordDataTests(unittest.TestCase):
    def test_holds_text_and_word_count(self) -> None:
        data = WordData(text="one two", word_count=2)
        self.assertEqual(data.text, "one two")
        self.assertEqual(data.word_count, 2)


class GatewayErrorTests(unittest.TestCase):
    def test_message_is_the_tool_error(self) -> None:
        error = GatewayError("Text is missing.")
        self.assertIsInstance(error, ToolError)
        self.assertEqual(str(error), "Text is missing.")


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
