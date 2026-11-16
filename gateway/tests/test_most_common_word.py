import asyncio
import unittest

from mcp import Client
from mcp.shared.exceptions import MCPError

from gateway.errors import needs_approval
from gateway.middleware import NEEDS_APPROVAL_CODE
from gateway.server import mcp
from gateway.tools.most_common_word import (
    MOST_COMMON_COUNT_DESCRIPTION,
    MOST_COMMON_TOOL_DESCRIPTION,
    MOST_COMMON_WORD_DESCRIPTION,
    most_common_word,
)
from gateway.tools.text import TEXT_DESCRIPTION


def _run(coro):
    return asyncio.run(coro)


class MostCommonWordTests(unittest.TestCase):
    def test_call_needs_human_approval(self) -> None:
        async def call() -> None:
            async with Client(mcp) as client:
                with self.assertRaises(MCPError) as caught:
                    await client.call_tool(
                        "most_common_word", {"text": "  one\ttwo\none  "}
                    )
            self.assertEqual(str(caught.exception), needs_approval("most_common_word"))
            self.assertEqual(caught.exception.code, NEEDS_APPROVAL_CODE)

        _run(call())

    def test_listed_descriptions_match_the_constants(self) -> None:
        async def listed() -> tuple[str | None, str]:
            async with Client(mcp) as client:
                page = await client.list_tools()
            tool = next(tool for tool in page.tools if tool.name == "most_common_word")
            text = tool.input_schema["properties"]["text"]["description"]
            return tool.description, text

        self.assertEqual(
            _run(listed()), (MOST_COMMON_TOOL_DESCRIPTION, TEXT_DESCRIPTION)
        )
        self.assertEqual(most_common_word.__doc__, MOST_COMMON_TOOL_DESCRIPTION)

    def test_output_schema_is_most_common_word(self) -> None:
        async def schema() -> dict:
            async with Client(mcp) as client:
                page = await client.list_tools()
            tool = next(tool for tool in page.tools if tool.name == "most_common_word")
            return tool.output_schema

        self.assertEqual(
            _run(schema()),
            {
                "description": MOST_COMMON_WORD_DESCRIPTION,
                "properties": {
                    "word": {
                        "description": MOST_COMMON_WORD_DESCRIPTION,
                        "title": "Word",
                        "type": "string",
                    },
                    "count": {
                        "description": MOST_COMMON_COUNT_DESCRIPTION,
                        "title": "Count",
                        "type": "integer",
                    },
                },
                "required": ["word", "count"],
                "title": "MostCommonWord",
                "type": "object",
            },
        )


if __name__ == "__main__":
    unittest.main()
