# Changelog

## 31 October 2026

`count_words` returns a `WordCount`. `count` is an integer with a minimum of 0. For `{"text": "one two three"}`, `structured_content` is `{"count": 3}`. The `content` text is `{`, a newline, two spaces, `"count": 3`, a newline, and `}`.

On 27 October 2026, `structured_content` for that input was `{"result": 3}`. The `content` text was `3`. [First call](traces/first-call.md) records that run. [Word count response](traces/word-count-response.md) records the 31 October run.

`count_words` raises `TypeError` when a caller invokes it directly and the argument is not a string. The function raises that error before `text.strip()`. The server checks `text` against the tool schema. The server rejects a non-string before `count_words` runs.

`reference.md` documents the `WordCount` schema. `tests/test_tools.py` checks the `content` text and `output_schema`. `evals/count_words_eval.py` reads `WordCount.count`.
