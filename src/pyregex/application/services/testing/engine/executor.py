from __future__ import annotations
from typing import List
import re
from pyregex.application.services.testing.base import MatchResult


class RegexExecutor:
    """Core regex execution engine."""

    def __init__(self, pattern: str, flags: int = 0):
        self.pattern_str = pattern
        self.flags = flags
        try:
            self.pattern = re.compile(pattern, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex: {e}")

    def execute_on_line(self, line: str, line_num: int) -> List[MatchResult]:
        """Finds all global matches in a single line."""
        results = []
        for match in self.pattern.finditer(line):
            res = MatchResult(
                pattern=self.pattern_str,
                span=match.span(),
                value=match.group(),
                groups=list(match.groups()),
                named_groups=match.groupdict(),
                line_number=line_num,
                context=line,
            )
            results.append(res)
        return results
