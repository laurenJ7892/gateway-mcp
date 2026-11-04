from typing import Annotated

from mcp.server import MCPServer
from pydantic import BaseModel, Field

from gateway.middleware import MaxConcurrentCalls, TimingLog

# len(text) counts characters. max_length rejects a longer string before split().
MAX_TEXT_LENGTH = 100_000
TOOL_DESCRIPTION = "Count words by splitting on whitespace."
TEXT_DESCRIPTION = "Text to count. Words are split on whitespace."
WORD_COUNT_DESCRIPTION = "How many words the text contains."
COUNT_DESCRIPTION = "Words in the text, split on whitespace."

mcp = MCPServer(
    "Word Counter",
    middleware=[TimingLog(), MaxConcurrentCalls(4)],
)


class WordCount(BaseModel):
    __doc__ = WORD_COUNT_DESCRIPTION

    count: Annotated[
        int,
        Field(description=COUNT_DESCRIPTION, ge=0),
    ]


@mcp.tool(description=TOOL_DESCRIPTION)
def count_words(
    text: Annotated[
        str,
        Field(
            description=TEXT_DESCRIPTION,
            max_length=MAX_TEXT_LENGTH,
        ),
    ],
) -> WordCount:
    if not isinstance(text, str):
        raise TypeError("text must be a string.")
    return WordCount(count=len(text.strip().split()))


count_words.__doc__ = TOOL_DESCRIPTION


if __name__ == "__main__":
    mcp.run()
