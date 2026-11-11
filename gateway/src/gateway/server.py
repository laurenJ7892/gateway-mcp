from mcp.server import MCPServer

from gateway.middleware import MaxConcurrentCalls, TimingLog
from gateway.tools.count_words import WORD_COUNT_TOOL_DESCRIPTION, count_words
from gateway.tools.most_common_word import (
    MOST_COMMON_TOOL_DESCRIPTION,
    most_common_word,
)

mcp = MCPServer(
    "Word Counter",
    middleware=[TimingLog(), MaxConcurrentCalls(4)],
)

mcp.tool(description=WORD_COUNT_TOOL_DESCRIPTION)(count_words)
mcp.tool(description=MOST_COMMON_TOOL_DESCRIPTION)(most_common_word)


if __name__ == "__main__":
    mcp.run()
