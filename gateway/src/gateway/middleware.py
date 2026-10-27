"""Timing and concurrency limits for inbound calls."""

from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from typing import Any

import anyio
from errors import too_many_calls
from mcp.server.context import CallNext, HandlerResult, ServerRequestContext
from mcp.shared.exceptions import MCPError

logger = logging.getLogger("gateway.middleware")

# Implementation-defined JSON-RPC server error. The message is the caller-facing part.
_TOO_MANY_CALLS = -32000
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


def _subject(ctx: ServerRequestContext[Any, Any]) -> str:
    if ctx.method == _TOOL_CALL and isinstance(ctx.params, Mapping):
        name = ctx.params.get("name")
        if isinstance(name, str) and name:
            return name
    return ctx.method


def _elapsed_ms(started: float) -> float:
    return (time.perf_counter() - started) * 1000
