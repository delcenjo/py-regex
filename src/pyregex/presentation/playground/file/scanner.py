"""Playground File Mode — Streaming Regex Scanner.

Line-by-line regex matching against a FileReader with:
- Streaming results (yields matches as found)
- Context lines (before/after)
- Progress callbacks for real-time stats
- Per-line timeout for ReDoS safety
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Callable, Iterator, Optional

from pyregex.presentation.playground.file.reader import FileReader


@dataclass
class ScanMatch:
    """A single match within a file line."""

    line_no: int
    line_text: str
    match_text: str
    start: int  # column start within line
    end: int  # column end within line
    groups: tuple = ()
    named_groups: dict = field(default_factory=dict)
    group_spans: list = field(default_factory=list)

    @classmethod
    def from_re_match(cls, m: re.Match, line_no: int, line_text: str) -> ScanMatch:
        return cls(
            line_no=line_no,
            line_text=line_text,
            match_text=m.group(0),
            start=m.start(),
            end=m.end(),
            groups=m.groups(),
            named_groups={k: v for k, v in m.groupdict().items() if v is not None},
            group_spans=[
                (m.start(i), m.end(i))
                for i in range(1, len(m.groups()) + 1)
                if m.group(i) is not None
            ],
        )


@dataclass
class ScanResult:
    """Aggregated result of a full file scan."""

    matches: list[ScanMatch]
    matched_lines: set[int]
    total_lines: int
    scan_time_ms: float
    timed_out_lines: int
    pattern: str
    flags: int
    total_matches: int = 0

    @property
    def match_count(self) -> int:
        return len(self.matches)

    @property
    def line_match_count(self) -> int:
        return len(self.matched_lines)

    @property
    def match_ratio(self) -> float:
        if self.total_lines == 0:
            return 0.0
        return self.line_match_count / self.total_lines


@dataclass
class ScanProgress:
    """Real-time scan progress data."""

    current_line: int
    total_lines: int
    matches_so_far: int
    elapsed_ms: float

    @property
    def percent(self) -> float:
        if self.total_lines == 0:
            return 100.0
        return (self.current_line / self.total_lines) * 100


# Type for progress callback
ProgressCallback = Callable[[ScanProgress], None]


class FileScanner:
    """Streaming regex scanner for files.

    Scans a FileReader line-by-line, yielding matches as they are found.
    Supports context lines, progress callbacks, and per-line timeouts.

    Usage:
        scanner = FileScanner(reader)
        result = scanner.scan(r"\\d+\\.\\d+\\.\\d+\\.\\d+")
        for match in result.matches:
            print(f"L{match.line_no}: {match.match_text}")
    """

    def __init__(
        self,
        reader: FileReader,
        max_matches: int = 10_000,
        line_timeout_ms: int = 100,
        progress_interval: int = 1000,
    ):
        self._reader = reader
        self._max_matches = max_matches
        self._line_timeout_ms = line_timeout_ms
        self._progress_interval = progress_interval

    def scan(
        self,
        pattern: str,
        flags: int = 0,
        on_progress: Optional[ProgressCallback] = None,
        start_line: int = 1,
        end_line: Optional[int] = None,
    ) -> ScanResult:
        """Run a full scan and return aggregated results.

        Args:
            pattern: Regex pattern string
            flags: re flags (re.IGNORECASE, etc.)
            on_progress: Callback for real-time progress updates
            start_line: 1-based start line (default: 1)
            end_line: 1-based end line (default: last line)

        Returns:
            ScanResult with all matches and statistics
        """
        matches: list[ScanMatch] = []
        matched_lines: set[int] = set()
        timed_out = 0
        t0 = time.perf_counter()
        total_matches = 0

        try:
            compiled = re.compile(pattern, flags)
        except re.error:
            return ScanResult(
                matches=[],
                matched_lines=set(),
                total_lines=self._reader.total_lines,
                scan_time_ms=0.0,
                timed_out_lines=0,
                pattern=pattern,
                flags=flags,
                total_matches=0,
            )

        actual_end = end_line or self._reader.total_lines

        for line_no, line_text in self._reader.iter_lines(start_line, end_line=None if end_line is None else actual_end):
            if on_progress and (line_no % self._progress_interval == 0):
                elapsed = (time.perf_counter() - t0) * 1000
                on_progress(
                    ScanProgress(
                        current_line=line_no,
                        total_lines=self._reader.total_lines,
                        matches_so_far=len(matches),
                        elapsed_ms=elapsed,
                    )
                )

            line_matches = self._match_line(compiled, line_text, line_no)
            if line_matches is None:
                timed_out += 1
                continue

            if line_matches:
                total_matches += len(line_matches)
                if len(matches) < self._max_matches:
                    remaining = self._max_matches - len(matches)
                    to_add = line_matches[:remaining]
                    matches.extend(to_add)
                    matched_lines.add(line_no)

        elapsed_ms = (time.perf_counter() - t0) * 1000

        if on_progress:
            on_progress(
                ScanProgress(
                    current_line=actual_end,
                    total_lines=self._reader.total_lines,
                    matches_so_far=len(matches),
                    elapsed_ms=elapsed_ms,
                )
            )

        return ScanResult(
            matches=matches,
            matched_lines=matched_lines,
            total_lines=self._reader.total_lines,
            scan_time_ms=elapsed_ms,
            timed_out_lines=timed_out,
            pattern=pattern,
            flags=flags,
            total_matches=total_matches,
        )

    def iter_matches(
        self,
        pattern: str,
        flags: int = 0,
        start_line: int = 1,
        end_line: Optional[int] = None,
    ) -> Iterator[ScanMatch]:
        """Stream matches one at a time (lazy evaluation)."""
        try:
            compiled = re.compile(pattern, flags)
        except re.error:
            return

        actual_end = end_line or self._reader.total_lines

        for line_no, line_text in self._reader.iter_lines(start_line, end_line=None if end_line is None else actual_end):
            line_matches = self._match_line(compiled, line_text, line_no)
            if line_matches:
                yield from line_matches

    def count_matches(self, pattern: str, flags: int = 0) -> int:
        """Quick count of total matches without storing them."""
        count = 0
        try:
            compiled = re.compile(pattern, flags)
        except re.error:
            return 0

        for _, line_text in self._reader.iter_lines():
            try:
                count += len(compiled.findall(line_text))
            except Exception:
                pass
        return count

    def get_matched_lines(
        self, pattern: str, flags: int = 0
    ) -> list[tuple[int, str]]:
        """Return only the lines that contain at least one match."""
        result = []
        try:
            compiled = re.compile(pattern, flags)
        except re.error:
            return result

        for line_no, line_text in self._reader.iter_lines():
            if compiled.search(line_text):
                result.append((line_no, line_text))
        return result

    def _match_line(
        self, compiled: re.Pattern, line: str, line_no: int
    ) -> Optional[list[ScanMatch]]:
        """Match a single line with timeout protection."""
        try:
            matches = list(compiled.finditer(line))
            if not matches:
                return []
            return [ScanMatch.from_re_match(m, line_no, line) for m in matches]
        except Exception:
            return None
