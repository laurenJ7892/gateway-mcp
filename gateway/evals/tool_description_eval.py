"""Checks the count_words descriptions that tools/list returns.

Cursor runs every eval from .cursor/hooks/tool-description-eval.sh when an
agent turn stops. That hook runs evals/run_evals.py. Run this eval by hand
from the gateway directory:

    uv run python evals/tool_description_eval.py

The script calls tools/list through the MCP client. That is the call Cursor
makes when it lists tools. A case passes when each listed description equals
the matching constant in count_words.py or text.py. A failed case names the constant. It does
not print the listed string.
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
from gateway.tools.text import TEXT_DESCRIPTION


def matches(label: str, actual: object, expected: str) -> str:
    if actual == expected:
        return f"pass  {label}"
    return f"fail  {label} does not match"


def text_description(schema: object) -> str:
    if not isinstance(schema, dict):
        return "fail  text description is missing"
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return "fail  text description is missing"
    text = properties.get("text")
    if not isinstance(text, dict):
        return "fail  text description is missing"
    return matches("text description", text.get("description"), TEXT_DESCRIPTION)


def output_descriptions(schema: object) -> list[str]:
    if not isinstance(schema, dict):
        return ["fail  output description is missing"]
    lines = [
        matches(
            "output description",
            schema.get("description"),
            WORD_COUNT_DESCRIPTION,
        )
    ]
    properties = schema.get("properties")
    count = properties.get("count") if isinstance(properties, dict) else None
    if not isinstance(count, dict):
        lines.append("fail  count description is missing")
        return lines
    lines.append(
        matches("count description", count.get("description"), COUNT_DESCRIPTION)
    )
    return lines


async def checks() -> list[str]:
    async with Client(mcp) as client:
        page = await client.list_tools()
    tool = next((item for item in page.tools if item.name == "count_words"), None)
    if tool is None:
        return ["fail  count_words is not registered"]
    return [
        matches("tool description", tool.description, WORD_COUNT_TOOL_DESCRIPTION),
        text_description(tool.input_schema),
        *output_descriptions(tool.output_schema),
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
