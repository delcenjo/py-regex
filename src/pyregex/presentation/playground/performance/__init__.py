"""Playground — Backtrack / ReDoS Detector.

Detects patterns vulnerable to catastrophic backtracking.
Now delegates to the deterministic ReDoS engine (NFA + AST analysis).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BacktrackReport:
    """Report from backtracking analysis."""

    risk_level: str = "none"  # none, low, medium, high, critical
    vulnerable: bool = False
    details: list[str] = field(default_factory=list)
    evil_input: Optional[str] = None  # input that triggers worst case
    estimated_time_ms: Optional[float] = None
    complexity: str = "O(N)"
    safe_rewrite: Optional[str] = None

    @property
    def icon(self) -> str:
        icons = {
            "none": "",
            "low": "",
            "medium": "",
            "high": "",
            "critical": "",
        }
        return icons.get(self.risk_level, "")


class BacktrackDetector:
    """
    Detects regex patterns vulnerable to catastrophic backtracking (ReDoS).

    Delegates to the deterministic ReDoS engine which uses:
    - NFA construction (Thompson algorithm)
    - AST-level overlap detection (CharSet bitsets)
    - Quantifier chain analysis
    - Anchor protection verification
    - NFA-guided pump generation
    """

    def __init__(self, test_timeout_ms: int = 2000):
        self.test_timeout_ms = test_timeout_ms
        self._analyzer = None

    @property
    def analyzer(self):
        if self._analyzer is None:
            try:
                from pyregex.domain.explain.redos import ReDoSAnalyzer

                self._analyzer = ReDoSAnalyzer(dynamic_timeout_ms=self.test_timeout_ms)
            except ImportError:
                self._analyzer = None
        return self._analyzer

    def analyze(self, pattern: str) -> BacktrackReport:
        """Full backtracking analysis using the ReDoS engine."""
        if not pattern:
            return BacktrackReport()

        if self.analyzer is None:
            return self._fallback_analyze(pattern)

        try:
            report = self.analyzer.analyze(pattern)

            # Convert ReDoSReport → BacktrackReport
            details: list[str] = []
            for v in report.vulnerabilities:
                details.append(f"{v.icon} {v.description}")

            risk_map = {
                "safe": "none",
                "low": "low",
                "medium": "medium",
                "high": "high",
                "critical": "critical",
            }

            return BacktrackReport(
                risk_level=risk_map.get(report.risk_level.value, "none"),
                vulnerable=report.is_vulnerable,
                details=details,
                evil_input=report.evil_input,
                complexity=report.complexity.notation,
                safe_rewrite=report.safe_rewrite,
            )
        except Exception:
            return self._fallback_analyze(pattern)

    def _fallback_analyze(self, pattern: str) -> BacktrackReport:
        """Minimal fallback if ReDoS engine is not available."""
        import re

        details = []
        risk = "none"

        # Basic nested quantifier check
        if re.search(r"\([^)]*[+*]\)\s*[+*]", pattern):
            details.append("Cuantificador anidado detectado")
            risk = "high"

        return BacktrackReport(
            risk_level=risk,
            vulnerable=risk in ("high", "critical"),
            details=details,
        )

    def format_report(self, report: BacktrackReport) -> list[str]:
        """Format report for display."""
        lines = [f"  {report.icon} Riesgo de backtracking: {report.risk_level.upper()}"]
        lines.append(f"  Complejidad: {report.complexity}")

        for d in report.details:
            lines.append(f"    {d}")

        if report.evil_input:
            lines.append(f'    Evil input: "{report.evil_input[:40]}..."')
        if report.estimated_time_ms:
            lines.append(f"    Tiempo estimado: {report.estimated_time_ms:.1f}ms")
        if report.safe_rewrite:
            lines.append(f"    Fix sugerido: {report.safe_rewrite}")

        return lines
