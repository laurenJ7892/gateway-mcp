from typing import Annotated

from mcp.server import MCPServer
from middleware import MaxConcurrentCalls, TimingLog
from pydantic import BaseModel, Field

# Characters, counted by len(text). Checked before split() builds a word list.
MAX_TEXT_LENGTH = 100_000

mcp = MCPServer(
    "Word Counter",
    middleware=[TimingLog(), MaxConcurrentCalls(4)],
)


class WordData(BaseModel):
    """Text and the word count of that text."""

    text: str = Field(description="The text that was counted.")
    word_count: int = Field(description="Words in the text, split on whitespace.")


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
    if isinstance(text, str) and len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"text is longer than {MAX_TEXT_LENGTH} characters.")
    return len(text.strip().split())


if __name__ == "__main__":
    mcp.run()
