"""Base class and infrastructure for all RegexBuilders.

Provides auto-validation, ReDoS safety checking, and self-documentation
capabilities for every builder in the PyRegex ecosystem.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Pattern


@dataclass
class BuilderMetadata:
    """Metadata for a regex builder to support UI, documentation, and discovery."""

    name: str
    category: str
    description: str
    examples: list[str] = field(default_factory=list)
    non_examples: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """Result of a single example validation."""

    input_text: str
    expected_match: bool
    actual_match: bool

    @property
    def passed(self) -> bool:
        return self.expected_match == self.actual_match


@dataclass
class ValidationReport:
    """Complete validation report for a builder."""

    builder_name: str
    pattern: str
    results: list[ValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def failures(self) -> list[ValidationResult]:
        return [r for r in self.results if not r.passed]

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"{status} [{self.builder_name}] "
            f"{self.total - len(self.failures)}/{self.total} checks passed | "
            f"Pattern: {self.pattern[:60]}..."
        )


@dataclass
class SafetyReport:
    """ReDoS safety analysis report for a builder's generated pattern."""

    builder_name: str
    pattern: str
    complexity: str = "O(N)"
    score: int = 0
    is_safe: bool = True
    vulnerabilities: list[str] = field(default_factory=list)

    def summary(self) -> str:
        icon = "" if self.is_safe else ""
        return f"{icon} [{self.builder_name}] {self.complexity} (score={self.score})"


class RegexBuilder(ABC):
    """Abstract base class for all regex builders.

    Every builder in the PyRegex ecosystem extends this class,
    gaining automatic self-validation, ReDoS safety checking,
    and pattern explanation capabilities.
    """

    @property
    @abstractmethod
    def metadata(self) -> BuilderMetadata:
        """Returns metadata for this builder."""
        pass

    @abstractmethod
    def build(self, config: dict[str, Any] | None = None) -> Pattern[str]:
        """Returns a compiled regex pattern object using the provided or default config."""
        pass

    @abstractmethod
    def default_config(self) -> dict[str, Any]:
        """Returns the default configuration values for this builder."""
        pass

    @abstractmethod
    def build_pattern(self) -> str:
        """Returns the raw regex pattern string (internal use)."""
        pass

    def build_compiled(self, flags: int = 0) -> Pattern[str]:
        """Returns a compiled regex pattern object (legacy support)."""
        return re.compile(self.build_pattern(), flags)

    def explain_params(self) -> dict[str, str]:
        """Returns a dictionary explaining the parameters (legacy support)."""
        return {}

    def validate(self) -> ValidationReport:
        """Auto-validate the generated pattern against metadata examples.

        Tests that all `metadata.examples` produce matches and all
        `metadata.non_examples` do NOT produce full matches.
        """
        pattern_str = self.build_pattern()
        report = ValidationReport(
            builder_name=self.metadata.name, pattern=pattern_str
        )

        try:
            compiled = re.compile(pattern_str)
        except re.error:
            report.results.append(
                ValidationResult(
                    input_text="<COMPILATION>",
                    expected_match=True,
                    actual_match=False,
                )
            )
            return report

        for example in self.metadata.examples:
            match = compiled.search(example)
            report.results.append(
                ValidationResult(
                    input_text=example,
                    expected_match=True,
                    actual_match=match is not None,
                )
            )

        for non_example in self.metadata.non_examples:
            match = compiled.fullmatch(non_example)
            report.results.append(
                ValidationResult(
                    input_text=non_example,
                    expected_match=False,
                    actual_match=match is not None,
                )
            )

        return report

    def safety_check(self) -> SafetyReport:
        """Run the ReDoS analyzer against the generated pattern.

        Returns a SafetyReport indicating whether the pattern is
        safe for production use or contains potential vulnerabilities.
        """
        pattern_str = self.build_pattern()
        report = SafetyReport(
            builder_name=self.metadata.name, pattern=pattern_str
        )

        try:
            from pyregex.domain.explain.redos import ReDoSAnalyzer

            analyzer = ReDoSAnalyzer()
            redos_report = analyzer.analyze(pattern_str)

            report.complexity = redos_report.complexity.notation
            report.score = redos_report.complexity.numeric_score
            report.is_safe = not redos_report.is_vulnerable
            report.vulnerabilities = [
                f"{v.icon} {v.description}" for v in redos_report.vulnerabilities
            ]
        except Exception:
            # If the ReDoS engine is unavailable, assume safe
            pass

        return report

    def explain(self) -> str:
        """Generate a human-readable explanation of the built pattern.

        Uses the AdvancedExplainer engine to produce a narrative
        description of what the regex matches.
        """
        pattern_str = self.build_pattern()

        try:
            from pyregex.domain.explain.engine import AdvancedExplainer

            explainer = AdvancedExplainer()
            result = explainer.explain(pattern_str, mode="detailed")
            if isinstance(result, dict):
                return result.get("explanation", str(result))
            return str(result)
        except Exception:
            return f"Pattern: {pattern_str}"
