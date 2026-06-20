"""Complexity Calculator — Big-O classification from vulnerability analysis.

Combines results from all analyzers to produce a final complexity
classification with a numeric score (0-100).
"""

from __future__ import annotations

from pyregex.domain.explain.redos.models import (
    Vulnerability,
    VulnType,
    Severity,
    ComplexityResult,
)


class ComplexityCalculator:
    """Calculates Big-O complexity from detected vulnerabilities."""

    TYPE_COMPLEXITY = {
        VulnType.NESTED_QUANTIFIER: "O(2^N)",
        VulnType.ADJACENT_OVERLAP: "O(N²)",
        VulnType.ALTERNATION_OVERLAP: "O(N²)",
        VulnType.QUANTIFIER_SUFFIX_OVERLAP: "O(N²)",
        VulnType.STAR_HEIGHT: "O(2^N)",
        VulnType.MULTIPLE_WILDCARDS: "O(N²)",
    }

    COMPLEXITY_ORDER = ["O(N)", "O(N²)", "O(N³)", "O(2^N)"]

    def calculate(
        self,
        vulnerabilities: list[Vulnerability],
        anchor_protected: bool = False,
        nfa_complexity: str = "O(N)",
    ) -> ComplexityResult:
        """Calculate final complexity from all analysis sources.

        Args:
            vulnerabilities: All detected vulnerabilities
            anchor_protected: Whether pattern is fully anchored (^...$)
            nfa_complexity: Complexity from NFA simulator
        """
        if not vulnerabilities:
            return ComplexityResult(
                notation="O(N)",
                numeric_score=10,
                explanation="Patrón lineal — sin riesgo de backtracking",
                anchor_protected=anchor_protected,
            )

        worst = "O(N)"
        for v in vulnerabilities:
            vuln_cx = self.TYPE_COMPLEXITY.get(v.type, "O(N)")
            worst = self._max_complexity(worst, vuln_cx)

        # 2 adjacent overlaps = O(N²), 3+ = O(N³)
        overlap_count = sum(
            1
            for v in vulnerabilities
            if v.type in (VulnType.ADJACENT_OVERLAP, VulnType.MULTIPLE_WILDCARDS)
        )
        if overlap_count >= 3 and worst == "O(N²)":
            worst = "O(N³)"

        worst = self._max_complexity(worst, nfa_complexity)

        score = self._notation_to_score(worst)

        # Anchor protection reduces score by ~20%
        if anchor_protected and worst != "O(2^N)":
            score = max(10, int(score * 0.8))

        explanation = self._explain(worst, vulnerabilities, anchor_protected)

        return ComplexityResult(
            notation=worst,
            numeric_score=score,
            explanation=explanation,
            anchor_protected=anchor_protected,
        )

    def _max_complexity(self, a: str, b: str) -> str:
        idx_a = self.COMPLEXITY_ORDER.index(a) if a in self.COMPLEXITY_ORDER else 0
        idx_b = self.COMPLEXITY_ORDER.index(b) if b in self.COMPLEXITY_ORDER else 0
        return self.COMPLEXITY_ORDER[max(idx_a, idx_b)]

    @staticmethod
    def _notation_to_score(notation: str) -> int:
        scores = {
            "O(N)": 10,
            "O(N²)": 55,
            "O(N³)": 75,
            "O(2^N)": 95,
        }
        return scores.get(notation, 50)

    @staticmethod
    def _explain(notation: str, vulns: list[Vulnerability], anchored: bool) -> str:
        parts = []

        if notation == "O(N)":
            parts.append("Complejidad lineal. Seguro para cualquier tamaño de entrada.")
        elif notation == "O(N²)":
            parts.append(
                "Complejidad cuadrática. Puede ser lento con entradas >10K caracteres."
            )
        elif notation == "O(N³)":
            parts.append("Complejidad cúbica. Será lento con entradas >1K caracteres.")
        elif notation == "O(2^N)":
            parts.append(
                "Complejidad exponencial (ReDoS confirmado). "
                "Con ~25 caracteres puede tardar horas."
            )

        if anchored:
            parts.append(
                "Patrón anclado con ^/$, lo que mitiga parcialmente el riesgo."
            )

        crit = sum(1 for v in vulns if v.severity >= Severity.HIGH)
        if crit:
            parts.append(f"{crit} vulnerabilidad(es) de alta severidad detectada(s).")

        return " ".join(parts)
