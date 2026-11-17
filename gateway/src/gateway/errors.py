"""Caller-facing errors."""


def too_many_calls(limit: int) -> str:
    return f"Too many calls are already running. The limit is {limit}."


def needs_approval(name: str) -> str:
    return f"{name} needs human approval."


def writes_blocked(name: str) -> str:
    return f"{name} is blocked in read-only mode."
