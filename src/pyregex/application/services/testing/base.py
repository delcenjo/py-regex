from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class MatchResult:
    """Detailed information about a single regex match."""

    pattern: str
    span: tuple[int, int]
    value: str
    groups: List[Optional[str]] = field(default_factory=list)
    named_groups: Dict[str, Optional[str]] = field(default_factory=dict)
    line_number: Optional[int] = None
    context: Optional[str] = None  # Surrounding text for visualization


@dataclass
class TestingState:
    """State of a testing session (matches, stats, errors)."""

    matches: List[MatchResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    total_lines: int = 0
    total_bytes: int = 0

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time


class TestingContext:
    """Configuration for a testing operation."""

    def __init__(self, flags: int = 0, max_matches: int = 1000):
        self.flags = flags
        self.max_matches = max_matches
        self.stop_on_first = False
