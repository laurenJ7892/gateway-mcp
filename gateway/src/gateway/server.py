from typing import Annotated

from mcp.server import MCPServer
from pydantic import BaseModel, Field

from gateway.middleware import MaxConcurrentCalls, TimingLog

# len(text) counts characters. max_length rejects a longer string before split().
MAX_TEXT_LENGTH = 100_000

mcp = MCPServer(
    "Word Counter",
    middleware=[TimingLog(), MaxConcurrentCalls(4)],
)


class WordCount(BaseModel):
    """How many words the text contains."""

    count: Annotated[
        int,
        Field(description="Words in the text, split on whitespace.", ge=0),
    ]


@mcp.tool()
def count_words(
    text: Annotated[
        str,
        Field(
            description="Text to count. Words are split on whitespace.",
            max_length=MAX_TEXT_LENGTH,
        ),
    ],
) -> WordCount:
    """Count words by splitting on whitespace."""
    if not isinstance(text, str):
        raise TypeError("text must be a string.")
    return WordCount(count=len(text.strip().split()))


if __name__ == "__main__":
    mcp.run()
