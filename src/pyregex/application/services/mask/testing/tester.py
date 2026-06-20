"""Regex testing engine to find matches in text or files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator


@dataclass
class MatchResult:
    """Represents a single regex match."""

    start: int
    end: int
    group: str
    line_number: int | None = None
    pattern_index: int = 0


@dataclass
class TestSummary:
    """Statistical summary of testing results."""

    total_matches: int
    lines_with_matches: int
    total_lines: int
    match_rate: float  # Percentage of lines with matches


class RegexTester:
    """Matches regex patterns against text or files."""

    def test_text(
        self, patterns: list[str], text: str, flags: int = 0
    ) -> tuple[list[MatchResult], TestSummary]:
        """Test multiple regex patterns against a string and return results + summary."""
        results = []
        total_lines = len(text.splitlines()) if text else 0
        lines_hit = set()

        for idx, pattern in enumerate(patterns):
            try:
                compiled = re.compile(pattern, flags)
                for match in compiled.finditer(text):
                    line_no = text.count("\n", 0, match.start()) + 1
                    lines_hit.add(line_no)

                    results.append(
                        MatchResult(
                            start=match.start(),
                            end=match.end(),
                            group=match.group(),
                            line_number=line_no,
                            pattern_index=idx,
                        )
                    )
            except re.error:
                continue

        summary = TestSummary(
            total_matches=len(results),
            lines_with_matches=len(lines_hit),
            total_lines=total_lines,
            match_rate=(len(lines_hit) / total_lines * 100) if total_lines > 0 else 0,
        )
        return sorted(results, key=lambda x: (x.start, x.end)), summary

    def test_line_by_line(
        self, patterns: list[str], text: str, flags: int = 0
    ) -> Iterator[tuple[int, str, list[MatchResult]]]:
        """Generator that tests text line by line and yields (line_no, line_content, matches)."""
        compiled_patterns = []
        for p in patterns:
            try:
                compiled_patterns.append(re.compile(p, flags))
            except re.error:
                continue

        for line_no, line in enumerate(text.splitlines(), 1):
            line_results = []
            for idx, compiled in enumerate(compiled_patterns):
                for match in compiled.finditer(line):
                    line_results.append(
                        MatchResult(
                            start=match.start(),
                            end=match.end(),
                            group=match.group(),
                            line_number=line_no,
                            pattern_index=idx,
                        )
                    )
            if line_results:
                yield line_no, line, sorted(line_results, key=lambda x: x.start)
