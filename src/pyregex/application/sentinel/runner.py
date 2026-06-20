"""Sentinel Engine — Test Suite Runner.

Orchestrates the execution of test cases, compiling the regex, generating
synthetic data, evaluating matches and assertions, and running coverage analysis.
"""

from __future__ import annotations
import re
import time
from typing import Optional

from pyregex.domain.sentinel.models import (
    TestSuite,
    TestCase,
    TestResult,
    TestStatus,
    SuiteResult,
)
from pyregex.domain.sentinel.coverage.tracker import CoverageTracker
from pyregex.domain.sentinel.generators.fuzzer import Fuzzer
from pyregex.domain.explain.lexer.scanner import Scanner
from pyregex.domain.explain.parser.recursive_descent import RecursiveDescentParser


class TestSuiteRunner:
    """Executes a defined TestSuite against a Regex Pattern."""

    def __init__(self, suite: TestSuite):
        self.suite = suite
        self.fuzzer = None
        if self.suite.fuzz_enabled:
            try:
                self.fuzzer = Fuzzer()
            except RuntimeError:
                pass  # Faker not installed

    def _parse_ast(self) -> Optional[CoverageTracker]:
        """Tries to parse the AST to enable coverage tracking."""
        try:
            scanner = Scanner(self.suite.pattern)
            tokens = scanner.tokenize()
            parser = RecursiveDescentParser(tokens)
            ast_root = parser.parse()
            return CoverageTracker(ast_root)
        except Exception:
            # Fallback if parsing fails (e.g. invalid regex or lookbehind not fully supported in AST)
            return None

    def _inject_synthetic_cases(self, cases: list[TestCase]) -> list[TestCase]:
        """Inject additional synthetic test cases from the fuzzer."""
        if not self.suite.fuzz_enabled or not self.suite.fuzz_types or not self.fuzzer:
            return cases

        new_cases = list(cases)
        amount_per_type = self.suite.fuzz_count // len(self.suite.fuzz_types)
        if amount_per_type < 1:
            amount_per_type = 1

        for ftype in self.suite.fuzz_types:
            synthetic_inputs = self.fuzzer.generate(ftype, amount_per_type)
            for inp in synthetic_inputs:
                new_cases.append(
                    TestCase(
                        input_text=inp,
                        should_match=False,
                        is_synthetic=True,
                        fuzzer_type=ftype,
                    )
                )

        garbage_inputs = self.fuzzer.generate("garbage", 10)
        for inp in garbage_inputs:
            new_cases.append(
                TestCase(
                    input_text=inp,
                    should_match=False,
                    is_synthetic=True,
                    fuzzer_type="garbage",
                )
            )

        return new_cases

    def run(self) -> SuiteResult:
        """Execute the test suite and return a detailed result."""
        compiled_regex = None
        error_msg = None

        try:
            compiled_regex = re.compile(self.suite.pattern)
        except re.error as e:
            error_msg = f"Regex Compilation Error: {e}"

        coverage_tracker = self._parse_ast()

        results: list[TestResult] = []
        start_time = time.perf_counter()

        all_cases = self._inject_synthetic_cases(self.suite.cases)

        for case in all_cases:
            if error_msg:
                results.append(
                    TestResult(
                        case=case,
                        status=TestStatus.ERROR,
                        execution_time_ms=0.0,
                        error_message=error_msg,
                    )
                )
                continue

            case_start = time.perf_counter()
            match = compiled_regex.search(case.input_text)
            case_time = (time.perf_counter() - case_start) * 1000.0

            did_match = match is not None
            status = TestStatus.PASS
            actual_groups: dict[str, str | None] = {}
            failure_reason = None

            if case.should_match and not did_match:
                status = TestStatus.FAIL
                failure_reason = "Expected match, but found none."
            elif not case.should_match and did_match:
                status = TestStatus.FAIL
                failure_reason = "Expected NO match, but found a match."
            elif did_match:
                assert match is not None
                actual_groups = match.groupdict()
                if case.expected_groups:
                    for key, expected_val in case.expected_groups.items():
                        actual_val = actual_groups.get(key)
                        if actual_val != expected_val:
                            status = TestStatus.FAIL
                            failure_reason = f"Group '{key}' mismatch. Expected '{expected_val}', got '{actual_val}'"
                            break

                if coverage_tracker and status == TestStatus.PASS:
                    coverage_tracker.process_match(case.input_text, match.span())

            results.append(
                TestResult(
                    case=case,
                    status=status,
                    execution_time_ms=case_time,
                    error_message=failure_reason,
                    matched_text=match.group(0) if did_match else None,
                    actual_groups=actual_groups,
                )
            )

        total_time_ms = (time.perf_counter() - start_time) * 1000.0

        coverage_report = None
        if coverage_tracker:
            coverage_report = coverage_tracker.generate_report()

        from pyregex.domain.sentinel.models import CoverageReport

        return SuiteResult(
            suite_name=self.suite.name,
            pattern=self.suite.pattern,
            results=results,
            coverage=coverage_report or CoverageReport(),
            total_execution_time_ms=total_time_ms,
        )
