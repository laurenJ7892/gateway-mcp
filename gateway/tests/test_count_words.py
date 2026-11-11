import asyncio
import unittest

from mcp import Client

from gateway.server import mcp
from gateway.tools.count_words import (
    COUNT_DESCRIPTION,
    WORD_COUNT_DESCRIPTION,
    WORD_COUNT_TOOL_DESCRIPTION,
    count_words,
)
from gateway.tools.text import MAX_TEXT_LENGTH, TEXT_DESCRIPTION


def _run(coro):
    return asyncio.run(coro)


def _count_text(count: int) -> str:
    return f'{{\n  "count": {count}\n}}'


class CountWordsTests(unittest.TestCase):
    def test_splits_on_whitespace(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "count_words", {"text": "  one\ttwo\nthree  "}
                )
            self.assertFalse(result.is_error)
            self.assertEqual(result.content[0].text, _count_text(3))
            return result.structured_content

        self.assertEqual(_run(call()), {"count": 3})

    def test_empty_text_is_zero(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool("count_words", {"text": "   \n"})
            self.assertFalse(result.is_error)
            self.assertEqual(result.content[0].text, _count_text(0))
            return result.structured_content

        self.assertEqual(_run(call()), {"count": 0})

    def test_text_at_the_maximum_is_counted(self) -> None:
        async def call() -> dict:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "count_words", {"text": "a" * MAX_TEXT_LENGTH}
                )
            self.assertFalse(result.is_error)
            self.assertEqual(result.content[0].text, _count_text(1))
            return result.structured_content

        self.assertEqual(_run(call()), {"count": 1})

    def test_text_over_the_maximum_is_rejected(self) -> None:
        async def call() -> None:
            async with Client(mcp) as client:
                result = await client.call_tool(
                    "count_words", {"text": "a" * (MAX_TEXT_LENGTH + 1)}
                )
            self.assertTrue(result.is_error)
            self.assertIsNone(result.structured_content)
            self.assertIn(str(MAX_TEXT_LENGTH), result.content[0].text)

        _run(call())

    def test_listed_descriptions_match_the_constants(self) -> None:
        async def listed() -> tuple[str | None, str]:
            async with Client(mcp) as client:
                page = await client.list_tools()
            tool = next(tool for tool in page.tools if tool.name == "count_words")
            text = tool.input_schema["properties"]["text"]["description"]
            return tool.description, text

        self.assertEqual(
            _run(listed()), (WORD_COUNT_TOOL_DESCRIPTION, TEXT_DESCRIPTION)
        )
        self.assertEqual(count_words.__doc__, WORD_COUNT_TOOL_DESCRIPTION)

    def test_registered_tools(self) -> None:
        async def names() -> set[str]:
            async with Client(mcp) as client:
                page = await client.list_tools()
            return {tool.name for tool in page.tools}

        self.assertEqual(_run(names()), {"count_words", "most_common_word"})

    def test_output_schema_is_word_count(self) -> None:
        async def schema() -> dict:
            async with Client(mcp) as client:
                page = await client.list_tools()
            tool = next(tool for tool in page.tools if tool.name == "count_words")
            return tool.output_schema

        self.assertEqual(
            _run(schema()),
            {
                "description": WORD_COUNT_DESCRIPTION,
                "properties": {
                    "count": {
                        "description": COUNT_DESCRIPTION,
                        "minimum": 0,
                        "title": "Count",
                        "type": "integer",
                    }
                },
                "required": ["count"],
                "title": "WordCount",
                "type": "object",
            },
        )


if __name__ == "__main__":
    unittest.main()
