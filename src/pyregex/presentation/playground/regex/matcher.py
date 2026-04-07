"""Playground — Live Matcher.

Runs regex matching with timeout protection and incremental mode for large inputs.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Iterator, Optional
import re
import time

from pyregex.presentation.playground.core.state import MatchInfo


@dataclass
class MatchResult:
    """Complete result of a matching operation."""

    matches: list[MatchInfo] = field(default_factory=list)
    match_count: int = 0
    time_us: float = 0.0
    timed_out: bool = False
    truncated: bool = False  # True if max_matches reached
    error: Optional[str] = None

    @property
    def has_matches(self) -> bool:
        return self.match_count > 0


class LiveMatcher:
    """
    Regex matcher with timeout protection and incremental mode.

    Features:
    - Timeout to prevent ReDoS hangs
    - Max match limit
    - Incremental matching for large texts
    - Match statistics
    """

    def __init__(self, timeout_ms: int = 500, max_matches: int = 1000):
        self.timeout_ms = timeout_ms
        self.max_matches = max_matches

    def match_all(self, pattern: re.Pattern, text: str) -> MatchResult:
        """Find all matches with timeout protection."""
        if not text:
            return MatchResult()

        matches: list[MatchInfo] = []
        start = time.perf_counter()
        deadline = start + (self.timeout_ms / 1000.0)
        timed_out = False
        truncated = False

        try:
            for m in pattern.finditer(text):
                if time.perf_counter() > deadline:
                    timed_out = True
                    break
                matches.append(MatchInfo.from_match(m))
                if len(matches) >= self.max_matches:
                    truncated = True
                    break
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1_000_000
            return MatchResult(error=str(e), time_us=elapsed)

        elapsed = (time.perf_counter() - start) * 1_000_000
        return MatchResult(
            matches=matches,
            match_count=len(matches),
            time_us=elapsed,
            timed_out=timed_out,
            truncated=truncated,
        )

    def match_first(self, pattern: re.Pattern, text: str) -> Optional[MatchInfo]:
        """Find only the first match (fast)."""
        try:
            m = pattern.search(text)
            return MatchInfo.from_match(m) if m else None
        except Exception:
            return None

    def match_fullmatch(self, pattern: re.Pattern, text: str) -> bool:
        """Check if the entire text matches."""
        try:
            return pattern.fullmatch(text) is not None
        except Exception:
            return False

    def match_incremental(
        self, pattern: re.Pattern, text: str, chunk_size: int = 10_000
    ) -> Iterator[MatchResult]:
        """
        Incremental matching for large texts.
        Yields partial results chunk by chunk.
        """
        if len(text) <= chunk_size:
            yield self.match_all(pattern, text)
            return

        # Process in overlapping chunks to avoid missing matches at boundaries
        overlap = min(1000, chunk_size // 10)
        pos = 0

        while pos < len(text):
            end = min(pos + chunk_size, len(text))
            chunk = text[pos:end]
            result = self.match_all(pattern, chunk)

            # Adjust match positions to absolute positions
            adjusted = []
            for m in result.matches:
                adjusted.append(
                    MatchInfo(
                        text=m.text,
                        start=m.start + pos,
                        end=m.end + pos,
                        groups=m.groups,
                        named_groups=m.named_groups,
                        group_spans=[(s + pos, e + pos) for s, e in m.group_spans],
                    )
                )

            yield MatchResult(
                matches=adjusted,
                match_count=len(adjusted),
                time_us=result.time_us,
                timed_out=result.timed_out,
            )

            pos = end - overlap if end < len(text) else len(text)

    def split(self, pattern: re.Pattern, text: str, max_split: int = 0) -> list[str]:
        """Split text by pattern."""
        try:
            return pattern.split(text, maxsplit=max_split)
        except Exception:
            return [text]

    def find_non_matches(
        self, pattern: re.Pattern, text: str
    ) -> list[tuple[int, int, str]]:
        """Find text segments that DON'T match — useful for debugging."""
        matches = list(pattern.finditer(text))
        if not matches:
            return [(0, len(text), text)] if text else []

        gaps = []
        prev_end = 0
        for m in matches:
            if m.start() > prev_end:
                gaps.append((prev_end, m.start(), text[prev_end : m.start()]))
            prev_end = m.end()

        if prev_end < len(text):
            gaps.append((prev_end, len(text), text[prev_end:]))

        return gaps

    def coverage(self, pattern: re.Pattern, text: str) -> float:
        """Calculate what percentage of the text is covered by matches."""
        if not text:
            return 0.0
        matched_chars = set()
        for m in pattern.finditer(text):
            for i in range(m.start(), m.end()):
                matched_chars.add(i)
        return len(matched_chars) / len(text) * 100.0
