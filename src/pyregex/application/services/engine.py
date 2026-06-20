from __future__ import annotations
import re
from typing import Any, Iterator, Match, Pattern
from pyregex.domain.builders.base import RegexBuilder


class RegexEngine:
    """Central engine for executing regex operations in PyRegex.

    Provides a high-level interface for common operations like match, findall,
    and finditer, with native support for builders and centralized flag management.
    """

    def __init__(self, pattern: str | Pattern[str], flags: int = 0):
        if isinstance(pattern, str):
            self.pattern = re.compile(pattern, flags)
        else:
            self.pattern = pattern
        self.flags = flags

    @classmethod
    def from_builder(
        cls, builder: RegexBuilder, config: dict[str, Any] | None = None, flags: int = 0
    ) -> RegexEngine:
        """Creates an engine instance from a regex builder and optional configuration."""
        compiled = builder.build(config)
        return cls(compiled, flags)

    def match(self, text: str) -> Match[str] | None:
        """Determine if the regex matches at the beginning of the string."""
        return self.pattern.match(text)

    def search(self, text: str) -> Match[str] | None:
        """Scan through string looking for the first location where the regex produces a match."""
        return self.pattern.search(text)

    def findall(self, text: str) -> list[Any]:
        """Return a list of all non-overlapping matches in the string."""
        return self.pattern.findall(text)

    def finditer(self, text: str) -> Iterator[Match[str]]:
        """Return an iterator yielding match objects for all non-overlapping matches."""
        return self.pattern.finditer(text)

    def sub(self, repl: str, text: str, count: int = 0) -> str:
        """Return the string obtained by replacing the leftmost non-overlapping occurrences of the pattern."""
        return self.pattern.sub(repl, text, count)

    def split(self, text: str, maxsplit: int = 0) -> list[str]:
        """Split text by the occurrences of the pattern."""
        return self.pattern.split(text, maxsplit)

    def get_pattern_string(self) -> str:
        return self.pattern.pattern


class RegexFlags:
    """Centralized management for common regex flags."""

    IGNORECASE = re.IGNORECASE
    MULTILINE = re.MULTILINE
    DOTALL = re.DOTALL
    VERBOSE = re.VERBOSE
    UNICODE = re.UNICODE

    @staticmethod
    def combine(*flags: int) -> int:
        """Combines multiple flags into a single integer bitmask."""
        result = 0
        for f in flags:
            result |= f
        return result
