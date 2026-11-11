from typing import Annotated

from pydantic import BaseModel, Field

from gateway.tools.lib import split_words
from gateway.tools.text import MAX_TEXT_LENGTH, TEXT_DESCRIPTION

WORD_COUNT_TOOL_DESCRIPTION = "Count words by splitting on whitespace."
WORD_COUNT_DESCRIPTION = "How many words the text contains."
COUNT_DESCRIPTION = "Words in the text, split on whitespace."


class WordCount(BaseModel):
    __doc__ = WORD_COUNT_DESCRIPTION

    count: Annotated[
        int,
        Field(description=COUNT_DESCRIPTION, ge=0),
    ]


def count_words(
    text: Annotated[
        str,
        Field(
            description=TEXT_DESCRIPTION,
            max_length=MAX_TEXT_LENGTH,
        ),
    ],
) -> WordCount:
    if not isinstance(text, str):
        raise TypeError("text must be a string.")
    return WordCount(count=len(split_words(text)))


count_words.__doc__ = WORD_COUNT_TOOL_DESCRIPTION
