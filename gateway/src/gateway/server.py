from typing import Annotated

from mcp.server import MCPServer
from middleware import MaxConcurrentCalls, TimingLog
from pydantic import Field

# len(text) counts characters. max_length rejects a longer string before split().
MAX_TEXT_LENGTH = 100_000

mcp = MCPServer(
    "Word Counter",
    middleware=[TimingLog(), MaxConcurrentCalls(4)],
)


@mcp.tool()
def count_words(
    text: Annotated[
        str,
        Field(
            description="Text to count. Words are split on whitespace.",
            max_length=MAX_TEXT_LENGTH,
        ),
    ],
) -> int:
    """Count words by splitting on whitespace."""
    return len(text.strip().split())


if __name__ == "__main__":
    mcp.run()
