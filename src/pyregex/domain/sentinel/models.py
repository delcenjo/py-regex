"""Sentinel Engine — Core Domain Models.

Data structures for the AST-based Regex Unit Testing Framework.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class TestStatus(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"


@dataclass
class TestCase:
    """A single test assertion against a regex pattern."""

    input_text: str
    should_match: bool  # True for `passes`, False for `fails`
    expected_spans: Optional[list[tuple[int, int]]] = None
    expected_groups: Optional[dict[str, str]] = None
    # Context injected by synthetic generators
    is_synthetic: bool = False
    fuzzer_type: Optional[str] = None


@dataclass
class TestResult:
    """The outcome of executing a single TestCase."""

    case: TestCase
    status: TestStatus
    execution_time_ms: float
    error_message: Optional[str] = None
    matched_text: Optional[str] = None
    actual_groups: dict[str, str] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return self.status == TestStatus.PASS


@dataclass
class CoverageReport:
    """Regex Code Coverage results based on AST node traversal."""

    total_branches: int = 0
    covered_branches: int = 0
    total_quantifiers: int = 0
    covered_quantifiers: int = 0

    # Detailed unexercised components
    missed_alternations: list[str] = field(default_factory=list)
    missed_quantifiers: list[str] = field(default_factory=list)

    @property
    def branch_coverage_percent(self) -> float:
        if self.total_branches == 0:
            return 100.0
        return (self.covered_branches / self.total_branches) * 100

    @property
    def quantifier_coverage_percent(self) -> float:
        if self.total_quantifiers == 0:
            return 100.0
        return (self.covered_quantifiers / self.total_quantifiers) * 100

    @property
    def overall_coverage(self) -> float:
        total = self.total_branches + self.total_quantifiers
        covered = self.covered_branches + self.covered_quantifiers
        if total == 0:
            return 100.0
        return (covered / total) * 100


@dataclass
class SuiteResult:
    """The complete outcome of executing a TestSuite."""

    suite_name: str
    pattern: str
    results: list[TestResult] = field(default_factory=list)
    coverage: CoverageReport = field(default_factory=CoverageReport)
    total_execution_time_ms: float = 0.0

    @property
    def total_tests(self) -> int:
        return len(self.results)

    @property
    def passed_tests(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_tests(self) -> int:
        return self.total_tests - self.passed_tests

    @property
    def success(self) -> bool:
        return self.failed_tests == 0


@dataclass
class TestSuite:
    """A collection of TestCases for a specific pattern."""

    name: str
    pattern: str
    cases: list[TestCase] = field(default_factory=list)
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    # Fuzzing configuration
    fuzz_enabled: bool = False
    fuzz_types: list[str] = field(default_factory=list)  # e.g., ["email", "ipv4"]
    fuzz_count: int = 100
