import unittest

from gateway.tools.lib import filter_alpha_words


class FilterAlphaWordsTests(unittest.TestCase):
    def test_strips_punctuation_and_keeps_letters(self) -> None:
        self.assertEqual(
            filter_alpha_words(["hello,", "world!"]),
            ["hello", "world"],
        )

    def test_keeps_digits_when_letters_remain(self) -> None:
        self.assertEqual(filter_alpha_words(["h3llo!"]), ["h3llo"])

    def test_drops_a_token_with_no_letters(self) -> None:
        self.assertEqual(filter_alpha_words(["!!!", "123", ""]), [])

    def test_keeps_only_the_tokens_that_have_letters(self) -> None:
        self.assertEqual(
            filter_alpha_words(["one", "...", "two,"]),
            ["one", "two"],
        )


if __name__ == "__main__":
    unittest.main()
