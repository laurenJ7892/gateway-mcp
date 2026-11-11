import asyncio
import json
import unittest

from mcp import Client

from gateway.server import mcp
from gateway.tools.most_common_word import (
    MOST_COMMON_COUNT_DESCRIPTION,
    MOST_COMMON_TOOL_DESCRIPTION,
    MOST_COMMON_WORD_DESCRIPTION,
    most_common_word,
)
from gateway.tools.text import MAX_TEXT_LENGTH, TEXT_DESCRIPTION


def _run(coro):
    return asyncio.run(coro)


def _result_text(word: str, count: int) -> str:
    return f'{{\n  "word": {json.dumps(word)},\n  "count": {count}\n}}'


class MostCommonWordTests(unittest.TestCase):
    def test_returns_the_most_common_word(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "most_common_word", {"text": "  one\ttwo\none  "}
                )
            self.assertFalse(result.is_error)
            self.assertEqual(result.content[0].text, _result_text("one", 2))
            return result.structured_content

        self.assertEqual(_run(call()), {"word": "one", "count": 2})

    def test_empty_text_has_no_word(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool("most_common_word", {"text": "   \n"})
            self.assertFalse(result.is_error)
            self.assertEqual(result.content[0].text, _result_text("", 0))
            return result.structured_content

        self.assertEqual(_run(call()), {"word": "", "count": 0})

    def test_tie_keeps_the_earliest_word(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "most_common_word", {"text": "hello, world!"}
                )
            self.assertFalse(result.is_error)
            self.assertEqual(result.content[0].text, _result_text("hello", 1))
            return result.structured_content

        self.assertEqual(_run(call()), {"word": "hello", "count": 1})

    def test_text_at_the_maximum_is_accepted(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "most_common_word", {"text": "a" * MAX_TEXT_LENGTH}
                )
            self.assertFalse(result.is_error)
            self.assertEqual(
                result.content[0].text, _result_text("a" * MAX_TEXT_LENGTH, 1)
            )
            return result.structured_content

        self.assertEqual(_run(call()), {"word": "a" * MAX_TEXT_LENGTH, "count": 1})

    def test_text_over_the_maximum_is_rejected(self) -> None:
        async def call() -> None:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "most_common_word", {"text": "a" * (MAX_TEXT_LENGTH + 1)}
                )
            self.assertTrue(result.is_error)
            self.assertIsNone(result.structured_content)
            self.assertIn(str(MAX_TEXT_LENGTH), result.content[0].text)

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
