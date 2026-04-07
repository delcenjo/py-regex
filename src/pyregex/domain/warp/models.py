"""Warp Profiler — Core Domain Models.

Data structures for representing empirical performance benchmarking
ticks, curves, and final profiles.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum


class ComplexityCurve(Enum):
    LINEAR = "O(N)"
    QUADRATIC = "O(N²)"
    CUBIC = "O(N³)"
    EXPONENTIAL = "O(2^N)"
    CONSTANT = "O(1)"
    UNKNOWN = "??"


@dataclass
class IterationTick:
    """A single benchmark data point."""

    input_length: int
    time_ms: float
    memory_alloc_bytes: int
    cpu_percent: float

    # Context
    is_timeout: bool = False
    is_match: bool = False


@dataclass
class BenchProfile:
    """The aggregate result of a profiling session for a pattern."""

    pattern: str
    ticks: list[IterationTick] = field(default_factory=list)

    # Statistical derivations
    base_complexity: ComplexityCurve = ComplexityCurve.UNKNOWN
    r_squared: float = 0.0

    # Overall metrics
    total_time_ms: float = 0.0
    max_memory_alloc_bytes: int = 0
    max_cpu_percent: float = 0.0

    timeout_hit: bool = False
    safe_to_run: bool = True
