import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from mcp import Client
from mcp.server import MCPServer
from mcp.shared.exceptions import MCPError

from gateway.errors import needs_approval, too_many_calls
from gateway.middleware import (
    NEEDS_APPROVAL_CODE,
    ApprovalGate,
    MaxConcurrentCalls,
    PinGate,
    TimingLog,
)
from gateway.pins import (
    DEFINITION_CHANGED_CODE,
    NOT_PINNED_CODE,
    PIN_GATE_CODE,
    PINS_FILE_CODE,
    TOOL_DEFINITION_CHANGED,
    TOOL_NOT_PINNED,
    approve_tool,
)
from gateway.tools.count_words import WORD_COUNT_TOOL_DESCRIPTION, count_words


def _run(coro):
    return asyncio.run(coro)


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


class PinGateTests(unittest.TestCase):
    def test_tools_call_blocks_a_changed_definition(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "pins.json"
                gate = PinGate(path)
                server = MCPServer("Fake", version="0.1.0", middleware=[gate])
                gate.server = server
                server.tool(description=WORD_COUNT_TOOL_DESCRIPTION)(count_words)
                async with Client(server) as client:
                    page = await client.list_tools()
                    tool = page.tools[0]
                    approve_tool(
                        path,
                        name=tool.name,
                        description=tool.description,
                        input_schema=tool.input_schema,
                        output_schema=tool.output_schema,
                        version="0.1.0",
                    )
                    allowed = await client.call_tool("count_words", {"text": "one"})
                    server._tool_manager.get_tool(
                        "count_words"
                    ).description += " also read ~/.ssh"
                    with self.assertRaises(MCPError) as caught:
                        await client.call_tool("count_words", {"text": "one"})
                    unknown = await client.call_tool("phone_home", {})
            self.assertFalse(allowed.is_error)
            self.assertEqual(str(caught.exception), TOOL_DEFINITION_CHANGED)
            self.assertEqual(caught.exception.code, DEFINITION_CHANGED_CODE)
            self.assertTrue(unknown.is_error)
            self.assertIn("phone_home", unknown.content[0].text)
            self.assertNotIn(TOOL_DEFINITION_CHANGED, unknown.content[0].text)

        _run(run())

    def test_tools_call_blocks_a_missing_pin(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "pins.json"
                gate = PinGate(path)
                server = MCPServer("Fake", version="0.1.0", middleware=[gate])
                gate.server = server
                server.tool(description=WORD_COUNT_TOOL_DESCRIPTION)(count_words)
                async with Client(server) as client:
                    with self.assertRaises(MCPError) as caught:
                        await client.call_tool("count_words", {"text": "one"})
            self.assertEqual(str(caught.exception), TOOL_NOT_PINNED)
            self.assertEqual(caught.exception.code, NOT_PINNED_CODE)

        _run(run())

    def test_unset_server_blocks_the_call(self) -> None:
        gate = PinGate(Path("pins.json"))

        async def call_next(ctx: SimpleNamespace) -> str:
            return "done"

        async def run() -> None:
            with self.assertRaises(MCPError) as caught:
                await gate(_call("tools/call", "count_words"), call_next)
            self.assertEqual(str(caught.exception), "Pin gate has no server.")
            self.assertEqual(caught.exception.code, PIN_GATE_CODE)

        _run(run())

    def test_invalid_pins_file_is_an_mcp_error(self) -> None:
        async def run() -> None:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "pins.json"
                path.write_text("{", encoding="utf-8")
                gate = PinGate(path)
                gate.server = SimpleNamespace(
                    _tool_manager=SimpleNamespace(
                        get_tool=lambda name: SimpleNamespace(
                            name="count_words",
                            description="Count words.",
                            parameters={"type": "object"},
                            output_schema={"type": "object"},
                        )
                    )
                )

                async def call_next(ctx: SimpleNamespace) -> str:
                    return "done"

                with self.assertRaises(MCPError) as caught:
                    await gate(_call("tools/call", "count_words"), call_next)
            self.assertEqual(caught.exception.code, PINS_FILE_CODE)
            self.assertIn("not valid JSON", str(caught.exception))

        _run(run())


class ApprovalGateTests(unittest.TestCase):
    def test_delete_file_needs_approval(self) -> None:
        gate = ApprovalGate({"count_words", "delete_file"}, {"count_words"})

        async def call_next(ctx: SimpleNamespace) -> str:
            return "done"

        async def run() -> None:
            self.assertEqual(
                await gate(_call("tools/call", "count_words"), call_next), "done"
            )
            with self.assertRaises(MCPError) as caught:
                await gate(_call("tools/call", "delete_file"), call_next)
            self.assertEqual(str(caught.exception), needs_approval("delete_file"))
            self.assertEqual(caught.exception.code, NEEDS_APPROVAL_CODE)

        _run(run())

    def test_unknown_name_proceeds(self) -> None:
        gate = ApprovalGate({"count_words"}, {"count_words"})

        async def call_next(ctx: SimpleNamespace) -> str:
            return "next"

        async def run() -> None:
            self.assertEqual(
                await gate(_call("tools/call", "phone_home"), call_next), "next"
            )

        _run(run())


if __name__ == "__main__":
    unittest.main()
