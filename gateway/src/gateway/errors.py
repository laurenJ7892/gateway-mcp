"""Caller-facing errors."""


def too_many_calls(limit: int) -> str:
    return f"Too many calls are already running. The limit is {limit}."
