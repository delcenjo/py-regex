# src/pyregex/domain/explain/models/tokens.py
from __future__ import annotations
from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """Enumeration of all possible lexical tokens in a Regular Expression."""

    LITERAL = auto()  # a, b, \n, \t, etc.
    DOT = auto()  # .

    START_ANCHOR = auto()  # ^ or \A
    END_ANCHOR = auto()  # $ or \Z or \z
    WORD_BOUNDARY = auto()  # \b or \B

    QUANTIFIER = auto()  # *, +, ?, {n}, {n,m}
    LAZY_MODIFIER = auto()  # ? immediately following a quantifier

    GROUP_START = auto()  # (, (?:, (?P<name>, (?=, (?!, (?<=, (?<!
    GROUP_END = auto()  # )

    CLASS_START = auto()  # [ or [^
    CLASS_END = auto()  # ]
    CLASS_RANGE = auto()  # - inside a character class

    ALTERNATION = auto()  # |

    CHAR_CLASS = auto()  # \d, \D, \w, \W, \s, \S
    BACKREFERENCE = auto()  # \1, \g<1>, \g<name>

    FLAG_SET = auto()  # (?i), (?m), (?-i)

    EOF = auto()  # End of the pattern string


@dataclass(frozen=True)
class Token:
    """A discrete lexical element of a regular expression."""

    type: TokenType
    value: str
    start: int
    end: int

    def __repr__(self) -> str:
        return f"<Token {self.type.name} '{self.value}' [{self.start}:{self.end}]>"
