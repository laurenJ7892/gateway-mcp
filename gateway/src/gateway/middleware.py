"""Timing, pin checks, approval, and concurrency limits for inbound calls."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import anyio
from mcp.server.context import CallNext, HandlerResult, ServerRequestContext
from mcp.shared.exceptions import MCPError

from gateway.errors import needs_approval, too_many_calls
from gateway.pins import (
    DEFINITION_CHANGED_CODE,
    NOT_PINNED_CODE,
    PIN_GATE_CODE,
    PINS_FILE_CODE,
    TOOL_DEFINITION_CHANGED,
    TOOL_NOT_PINNED,
    PinsFileError,
    block_reason,
)

logger = logging.getLogger("gateway.middleware")

# Implementation-defined JSON-RPC server errors. The caller reads the message.
# Each failure has its own code.
_TOO_MANY_CALLS = -32000
NEEDS_APPROVAL_CODE = -32005
_PIN_CODES = {
    TOOL_DEFINITION_CHANGED: DEFINITION_CHANGED_CODE,
    TOOL_NOT_PINNED: NOT_PINNED_CODE,
}
_TOOL_CALL = "tools/call"


class TimingLog:
    """Log how long each inbound message takes."""

    async def __call__(
        self,
        ctx: ServerRequestContext[Any, Any],
        call_next: CallNext,
    ) -> HandlerResult:
        started = time.perf_counter()
        try:
            result = await call_next(ctx)
        except Exception:
            logger.info("%s failed in %.2fms", _subject(ctx), _elapsed_ms(started))
            raise
        logger.info("%s completed in %.2fms", _subject(ctx), _elapsed_ms(started))
        return result


class PinGate:
    """Block a tools/call whose registered definition is not the saved pin.

    Set `server` to the MCP server after it is constructed. A tools/call
    before that set raises. A name that server does not register proceeds
    to the next handler.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.server: Any = None

    async def __call__(
        self,
        ctx: ServerRequestContext[Any, Any],
        call_next: CallNext,
    ) -> HandlerResult:
        if ctx.method != _TOOL_CALL:
            return await call_next(ctx)
        if self.server is None:
            raise MCPError(PIN_GATE_CODE, "Pin gate has no server.")
        tool = _registered_tool(self.server, _tool_name(ctx))
        if tool is None:
            return await call_next(ctx)
        try:
            reason = block_reason(
                self.path,
                name=tool.name,
                description=tool.description,
                input_schema=tool.parameters,
                output_schema=tool.output_schema,
            )
        except PinsFileError as exc:
            raise MCPError(PINS_FILE_CODE, str(exc)) from exc
        if reason is not None:
            raise MCPError(_PIN_CODES[reason], reason)
        return await call_next(ctx)


class ApprovalGate:
    """Require approval for a registered tool that is not in the open set."""

    def __init__(self, registered: set[str], no_approval: set[str]) -> None:
        self.registered = set(registered)
        self.no_approval = set(no_approval)

    async def __call__(
        self,
        ctx: ServerRequestContext[Any, Any],
        call_next: CallNext,
    ) -> HandlerResult:
        if ctx.method != _TOOL_CALL:
            return await call_next(ctx)
        name = _tool_name(ctx)
        if name is None or name not in self.registered or name in self.no_approval:
            return await call_next(ctx)
        raise MCPError(NEEDS_APPROVAL_CODE, needs_approval(name))


class MaxConcurrentCalls:
    """Refuse a tool call when `limit` calls are already running."""

    def __init__(self, limit: int) -> None:
        if limit < 1:
            raise ValueError("limit must be at least 1")
        self.limit = limit
        self._active = 0
        self._lock = anyio.Lock()

    async def __call__(
        self,
        ctx: ServerRequestContext[Any, Any],
        call_next: CallNext,
    ) -> HandlerResult:
        if ctx.method != _TOOL_CALL:
            return await call_next(ctx)

        async with self._lock:
            if self._active >= self.limit:
                raise MCPError(_TOO_MANY_CALLS, too_many_calls(self.limit))
            self._active += 1
        try:
            return await call_next(ctx)
        finally:
            async with self._lock:
                self._active -= 1


def _tool_name(ctx: ServerRequestContext[Any, Any]) -> str | None:
    if isinstance(ctx.params, Mapping):
        name = ctx.params.get("name")
        if isinstance(name, str) and name:
            return name
    return None


def _registered_tool(server: Any, name: str | None) -> Any:
    if name is None:
        return None
    return server._tool_manager.get_tool(name)


def _subject(ctx: ServerRequestContext[Any, Any]) -> str:
    if ctx.method == _TOOL_CALL:
        name = _tool_name(ctx)
        if name is not None:
            return name
    return ctx.method


def _elapsed_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000
