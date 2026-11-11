from collections import Counter


def split_words(text: str):
    return text.strip().split()


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
