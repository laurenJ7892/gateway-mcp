from typing import Annotated

from pydantic import BaseModel, Field

from gateway.tools.lib import find_most_common_word_used, split_text_count, split_words
from gateway.tools.text import MAX_TEXT_LENGTH, TEXT_DESCRIPTION

MOST_COMMON_WORD_DESCRIPTION = "The most common word in the text."
MOST_COMMON_COUNT_DESCRIPTION = (
    "How many times the most common word appeared in the text."
)
MOST_COMMON_TOOL_DESCRIPTION = "Find most common word in the text."


class MostCommonWord(BaseModel):
    __doc__ = MOST_COMMON_WORD_DESCRIPTION

    word: Annotated[
        str,
        Field(description=MOST_COMMON_WORD_DESCRIPTION),
    ]

    count: Annotated[
        int,
        Field(description=MOST_COMMON_COUNT_DESCRIPTION),
    ]


def most_common_word(
    text: Annotated[
        str,
        Field(
            description=TEXT_DESCRIPTION,
            max_length=MAX_TEXT_LENGTH,
        ),
    ],
) -> MostCommonWord:
    if not isinstance(text, str):
        raise TypeError("text must be a string.")

    split_text = split_words(text)
    if not split_text:
        return MostCommonWord(word="", count=0)

    text_counter = split_text_count(split_text)
    word, count = find_most_common_word_used(text_counter)
    return MostCommonWord(word=word, count=count)


most_common_word.__doc__ = MOST_COMMON_TOOL_DESCRIPTION
