"""Run every eval.

Run this from the gateway directory:

    uv run python evals/run_evals.py

The runner prints each script's lines. It exits with status code 1 when any
script fails. Each eval still runs on its own.
"""

from __future__ import annotations

import sys

import count_words_eval
import most_common_word_eval
import tool_description_eval

EVALS = (
    count_words_eval,
    most_common_word_eval,
    tool_description_eval,
)


def main() -> int:
    failed = 0
    for module in EVALS:
        print(f"{module.__name__}.py")
        if module.main() != 0:
            failed += 1
        print()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
