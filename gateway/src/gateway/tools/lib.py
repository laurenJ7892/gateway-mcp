import string
from collections import Counter


def filter_alpha_words(words: list[str]) -> list[str]:
    kept: list[str] = []
    for word in words:
        without_punctuation = "".join(
            character for character in word if character not in string.punctuation
        )
        if any(character.isalpha() for character in without_punctuation):
            kept.append(without_punctuation)
    return kept


def split_words(text: str):
    return text.split()


def split_text_count(split_text: list[str]) -> Counter[str]:
    return Counter(split_text)


# Picks the first one when there is a tie
def find_most_common_word_used(
    counter: Counter[str],
) -> tuple[str, int]:
    most_common_array = counter.most_common(1)
    if not most_common_array:
        raise ValueError("No word found to be the most common.")

    word, count = most_common_array[0]
    return word, count
