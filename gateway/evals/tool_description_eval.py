"""Checks the tool descriptions that tools/list returns.

Cursor runs every eval from .cursor/hooks/tool-description-eval.sh when an
agent turn stops. That hook runs evals/run_evals.py. Run this eval by hand
from the gateway directory:

    uv run python evals/tool_description_eval.py

The script calls tools/list through the MCP client. That is the call Cursor
makes when it lists tools. A case passes when each listed description equals
the matching constant in count_words.py, most_common_word.py, or text.py. A
failed case names the constant. It does not print the listed string.
"""

from __future__ import annotations

import asyncio
import sys

from mcp import Client

from gateway.server import mcp
from gateway.tools.count_words import (
    COUNT_DESCRIPTION,
    WORD_COUNT_DESCRIPTION,
    WORD_COUNT_TOOL_DESCRIPTION,
)
from gateway.tools.most_common_word import (
    MOST_COMMON_COUNT_DESCRIPTION,
    MOST_COMMON_TOOL_DESCRIPTION,
    MOST_COMMON_WORD_DESCRIPTION,
)
from gateway.tools.text import TEXT_DESCRIPTION


def matches(label: str, actual: object, expected: str) -> str:
    if actual == expected:
        return f"pass  {label}"
    return f"fail  {label} does not match"


def text_description(schema: object, label: str) -> str:
    if not isinstance(schema, dict):
        return f"fail  {label} is missing"
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return f"fail  {label} is missing"
    text = properties.get("text")
    if not isinstance(text, dict):
        return f"fail  {label} is missing"
    return matches(label, text.get("description"), TEXT_DESCRIPTION)


def output_field(schema: object, field: str, label: str, expected: str) -> str:
    if not isinstance(schema, dict):
        return f"fail  {label} is missing"
    properties = schema.get("properties")
    item = properties.get(field) if isinstance(properties, dict) else None
    if not isinstance(item, dict):
        return f"fail  {label} is missing"
    return matches(label, item.get("description"), expected)


def count_words_lines(tool: object) -> list[str]:
    if tool is None:
        return ["fail  count_words is not registered"]
    return [
        matches(
            "count_words tool description",
            tool.description,
            WORD_COUNT_TOOL_DESCRIPTION,
        ),
        text_description(tool.input_schema, "count_words text description"),
        matches(
            "count_words output description",
            tool.output_schema.get("description")
            if isinstance(tool.output_schema, dict)
            else None,
            WORD_COUNT_DESCRIPTION,
        ),
        output_field(
            tool.output_schema,
            "count",
            "count_words count description",
            COUNT_DESCRIPTION,
        ),
    ]


def most_common_word_lines(tool: object) -> list[str]:
    if tool is None:
        return ["fail  most_common_word is not registered"]
    output = tool.output_schema if isinstance(tool.output_schema, dict) else None
    return [
        matches(
            "most_common_word tool description",
            tool.description,
            MOST_COMMON_TOOL_DESCRIPTION,
        ),
        text_description(tool.input_schema, "most_common_word text description"),
        matches(
            "most_common_word output description",
            None if output is None else output.get("description"),
            MOST_COMMON_WORD_DESCRIPTION,
        ),
        output_field(
            tool.output_schema,
            "word",
            "most_common_word word description",
            MOST_COMMON_WORD_DESCRIPTION,
        ),
        output_field(
            tool.output_schema,
            "count",
            "most_common_word count description",
            MOST_COMMON_COUNT_DESCRIPTION,
        ),
    ]


async def checks() -> list[str]:
    async with Client(mcp) as client:
        page = await client.list_tools()
    by_name = {item.name: item for item in page.tools}
    return [
        *count_words_lines(by_name.get("count_words")),
        *most_common_word_lines(by_name.get("most_common_word")),
    ]


def main() -> int:
    lines = asyncio.run(checks())
    failed = 0
    for line in lines:
        print(line)
        if line.startswith("fail"):
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
