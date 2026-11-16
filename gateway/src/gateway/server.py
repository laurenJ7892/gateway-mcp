from mcp.server import MCPServer

from gateway.middleware import MaxConcurrentCalls, PinGate, TimingLog
from gateway.pins import default_pins_path
from gateway.tools.count_words import WORD_COUNT_TOOL_DESCRIPTION, count_words
from gateway.tools.most_common_word import (
    MOST_COMMON_TOOL_DESCRIPTION,
    most_common_word,
)

pin_gate = PinGate(default_pins_path())
mcp = MCPServer(
    "Word Counter",
    version="0.1.0",
    middleware=[TimingLog(), pin_gate, MaxConcurrentCalls(4)],
)
pin_gate.server = mcp

mcp.tool(description=WORD_COUNT_TOOL_DESCRIPTION)(count_words)
mcp.tool(description=MOST_COMMON_TOOL_DESCRIPTION)(most_common_word)


if __name__ == "__main__":
    mcp.run()
