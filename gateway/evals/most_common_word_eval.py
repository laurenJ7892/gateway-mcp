"""Red-team checks for most_common_word.

Run this from the gateway directory:

    uv run python evals/most_common_word_eval.py

A case passes when most_common_word returns the expected word and count, or
when most_common_word raises TypeError or ValueError. most_common_word(4)
raises TypeError. The script calls most_common_word directly. The huge-input
case reads max_length from the most_common_word parameter.
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

from gateway.tools.most_common_word import most_common_word

# "the" is the only repeated word. A tie keeps the earliest word.
INJECTION_WORD = "the"
INJECTION_COUNT = 2


def empty_string() -> str:
    result = most_common_word("")
    if result.word == "" and result.count == 0:
        return "pass  empty string returns '' 0"
    return f"fail  empty string returns {result.word!r} {result.count}"


def punctuation() -> str:
    result = most_common_word(PUNCTUATION)
    if result.word == "hello" and result.count == 1:
        return f"pass  {PUNCTUATION!r} returns 'hello' 1"
    return f"fail  {PUNCTUATION!r} returns {result.word!r} {result.count}"


def huge_input() -> str:
    limit = maximum_length(most_common_word)
    if limit is None:
        return "fail  most_common_word has no maximum length"
    return f"pass  maximum length is {limit}"


def wrong_type() -> str:
    return rejected_int(most_common_word)


def prompt_injection() -> str:
    result, opened = call_without_network(most_common_word, INJECTION)
    if opened:
        return f"fail  injection opened {opened[0]}"
    if result.word != INJECTION_WORD or result.count != INJECTION_COUNT:
        return f"fail  injection returns {result.word!r} {result.count}"
    return (
        f"pass  injection returns {INJECTION_WORD!r} {INJECTION_COUNT} and opens no URL"
    )


def tie_first_result_returned() -> str:
    result = most_common_word("cat dog, dog cat")
    if result.word == "cat" and result.count == 2:
        return "pass  first tie returned 'cat' 2"
    return f"fail  tie string returns {result.word!r} {result.count}"


def all_punctuation_returns_nothing() -> str:
    result = most_common_word("?>:,.-=:{} ?>:,.-=:{}")
    if result.word == "" and result.count == 0:
        return "pass  only punctuation returns nothing"
    return f"fail  only punctuation returns nothing {result.word!r} {result.count}"


def main() -> int:
    return run(
        (
            empty_string,
            punctuation,
            huge_input,
            wrong_type,
            prompt_injection,
            tie_first_result_returned,
            all_punctuation_returns_nothing,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
