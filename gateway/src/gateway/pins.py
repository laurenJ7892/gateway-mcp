"""Approved tool definitions.

Accept the current definition of a tool and update its pin:

    uv run python -m gateway.pins accept count_words
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

logger = logging.getLogger("gateway.pins")

# The tools/call reason when the listed definition is not the pinned one.
TOOL_DEFINITION_CHANGED = "tool_definition_changed"

# name, version, and hash, in that order, so the file stays easy to read.
_PIN_KEYS = ("name", "version", "hash")


def definition_hash(
    name: str,
    description: str | None,
    input_schema: Mapping[str, Any],
) -> str:
    """Hash one tool definition as SHA-256.

    The hashed text is JSON with sorted keys and no extra whitespace, so the
    same name, description, and input schema always hash the same.
    """
    payload = {
        "name": name,
        "description": description,
        "input_schema": input_schema,
    }
    encoded = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def default_pins_path() -> Path:
    """Return gateway/pins.json next to this package."""
    return Path(__file__).resolve().parents[2] / "pins.json"


def approve_tool(
    path: Path,
    *,
    name: str,
    description: str | None,
    input_schema: Mapping[str, Any],
    version: str | None,
    replace: bool = False,
) -> dict[str, Any]:
    """Save this tool the first time it is approved.

    A later approval keeps the saved record. `replace` writes the current
    definition over that record. `version` is the server version when the
    server reports one, and null when it does not.
    """
    pins = load_pins(path)
    existing = pins.get(name)
    if isinstance(existing, dict) and not replace:
        return existing
    record = {
        "name": name,
        "version": version if version else None,
        "hash": definition_hash(name, description, input_schema),
    }
    pins[name] = {key: record[key] for key in _PIN_KEYS}
    _write_pins(path, pins)
    return pins[name]


def block_reason(
    path: Path,
    *,
    name: str,
    description: str | None,
    input_schema: Mapping[str, Any],
) -> str | None:
    """Return `tool_definition_changed` when this tools/call must be blocked.

    The current definition is hashed again. A hash equal to the pin allows
    the call. A different hash, or no pin, blocks the call. The log line
    names the old hash and the new hash.
    """
    current = definition_hash(name, description, input_schema)
    pinned = _pinned_hash(load_pins(path), name)
    if pinned == current:
        return None
    logger.info(
        "%s %s old %s new %s",
        name,
        TOOL_DEFINITION_CHANGED,
        pinned if pinned is not None else "none",
        current,
    )
    return TOOL_DEFINITION_CHANGED


def load_pins(path: Path) -> dict[str, Any]:
    """Read the pins file. A missing file has no pins."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} does not hold tool pins")
    return data


def _pinned_hash(pins: Mapping[str, Any], name: str) -> str | None:
    record = pins.get(name)
    if not isinstance(record, dict):
        return None
    pinned = record.get("hash")
    if not isinstance(pinned, str) or not pinned:
        return None
    return pinned


def _write_pins(path: Path, pins: Mapping[str, Any]) -> None:
    text = json.dumps(pins, indent=2, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


async def _accept(path: Path, names: Sequence[str]) -> int:
    from mcp import Client

    from gateway.server import mcp

    failed = 0
    async with Client(mcp) as client:
        info = client.server_info
        version = None if info is None else info.version
        page = await client.list_tools()
        by_name = {tool.name: tool for tool in page.tools}
        for name in names:
            tool = by_name.get(name)
            if tool is None or tool.description is None:
                print(f"{name} is not listed", file=sys.stderr)
                failed += 1
                continue
            saved = approve_tool(
                path,
                name=tool.name,
                description=tool.description,
                input_schema=tool.input_schema,
                version=version,
                replace=True,
            )
            print(f"accepted {saved['name']} {saved['hash']}")
    return 1 if failed else 0


def main(argv: Sequence[str] | None = None) -> int:
    """Accept the current tools/list definition and update the pin."""
    parser = argparse.ArgumentParser(description="Update an approved tool pin.")
    parser.add_argument(
        "--pins",
        type=Path,
        default=default_pins_path(),
        help="Pins file. The default is gateway/pins.json.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    accept = commands.add_parser(
        "accept",
        help="Replace the pin with the current tool definition.",
    )
    accept.add_argument("name", nargs="+", help="Tool to accept.")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.command == "accept":
        return asyncio.run(_accept(args.pins, args.name))
    return 1


if __name__ == "__main__":
    sys.exit(main())
