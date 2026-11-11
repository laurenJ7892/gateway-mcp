"""Red-team checks for count_words.

Run this from the gateway directory:

    uv run python evals/count_words_eval.py

A case passes when count_words returns the expected count, or when count_words
raises TypeError or ValueError. count_words(4) raises TypeError. The script
calls count_words directly. The huge-input case reads max_length from the
count_words parameter.
"""

from __future__ import annotations

import sys

from checks import (
    INJECTION,
    PUNCTUATION,
    call_without_network,
    maximum_length,
    rejected_int,
    run,
)

from gateway.tools.count_words import count_words

INJECTION_WORDS = 13


def empty_string() -> str:
    result = count_words("").count
    if result == 0:
        return "pass  empty string returns 0"
    return f"fail  empty string returns {result}"


def punctuation() -> str:
    result = count_words(PUNCTUATION).count
    if result == 2:
        return f"pass {PUNCTUATION!r} returns 2"
    return f"fail  {PUNCTUATION!r} returns {result}"


def huge_input() -> str:
    limit = maximum_length(count_words)
    if limit is None:
        return "fail count_words has no maximum length"
    return f"pass  maximum length is {limit}"


def wrong_type() -> str:
    return rejected_int(count_words)


def prompt_injection() -> str:
    result, opened = call_without_network(count_words, INJECTION)
    if opened:
        return f"fail  injection opened {opened[0]}"
    if result.count != INJECTION_WORDS:
        return f"fail  injection returns {result.count}"
    return f"pass  injection returns {INJECTION_WORDS} and opens no URL"


def main() -> int:
    return run(
        (
            empty_string,
            punctuation,
            huge_input,
            wrong_type,
            prompt_injection,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
