from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from gateway.middleware import (
    ApprovalGate,
    MaxConcurrentCalls,
    PinGate,
    ReadOnlyMode,
    TimingLog,
)
from gateway.pins import default_pins_path
from gateway.tools.count_words import WORD_COUNT_TOOL_DESCRIPTION, count_words
from gateway.tools.most_common_word import (
    MOST_COMMON_TOOL_DESCRIPTION,
    most_common_word,
)

READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    open_world_hint=False,
)

pin_gate = PinGate(default_pins_path())
read_only = ReadOnlyMode()
mcp = MCPServer(
    "Word Counter",
    version="0.1.0",
    middleware=[
        TimingLog(),
        pin_gate,
        read_only,
        MaxConcurrentCalls(4),
        ApprovalGate(
            registered={"count_words", "most_common_word"},
            no_approval={"count_words"},
        ),
    ],
)
pin_gate.server = mcp
read_only.server = mcp

mcp.tool(description=WORD_COUNT_TOOL_DESCRIPTION, annotations=READ_ONLY)(count_words)
mcp.tool(description=MOST_COMMON_TOOL_DESCRIPTION, annotations=READ_ONLY)(
    most_common_word
)


if __name__ == "__main__":
    mcp.run()
