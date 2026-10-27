"""Caller-facing errors."""

from mcp.server.mcpserver.exceptions import ToolError


class GatewayError(ToolError):
    """A problem the caller can fix.

    The tool result is this message. The server does not add a traceback.
    """


def too_many_calls(limit: int) -> str:
    return f"Too many calls are already running. The limit is {limit}."
