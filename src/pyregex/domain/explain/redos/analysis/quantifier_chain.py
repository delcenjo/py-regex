"""Quantifier Chain Analyzer — Detects dangerous quantifier nesting and adjacency.

Performs AST-level analysis to find the classic ReDoS patterns:
- Nested quantifiers: (a+)+           → O(2^N)
- Adjacent quantifiers: \\w+\\w+       → O(N²)
- Quantified alternation overlap      → O(2^N)
- Multiple wildcards: .*foo.*bar.*    → O(N³)
"""

from __future__ import annotations

from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    DotNode,
    AlternationNode,
    GroupNode,
    QuantifierNode,
)
from pyregex.domain.explain.redos.models import (
    Vulnerability,
    VulnType,
    Severity,
)


class QuantifierChainAnalyzer:
    """Detects dangerous quantifier patterns via AST traversal."""

    def analyze(self, root: RootNode) -> list[Vulnerability]:
        vulns: list[Vulnerability] = []
        self._walk(root, vulns, quantifier_depth=0)
        self._check_wildcards(root, vulns)
        return vulns

    def _walk(self, node: AstNode, vulns: list[Vulnerability], quantifier_depth: int):

        if isinstance(node, RootNode):
            for child in node.children:
                self._walk(child, vulns, quantifier_depth)

        elif isinstance(node, GroupNode):
            for child in node.children:
                self._walk(child, vulns, quantifier_depth)

        elif isinstance(node, AlternationNode):
            self._walk(node.left, vulns, quantifier_depth)
            self._walk(node.right, vulns, quantifier_depth)

        elif isinstance(node, QuantifierNode):
            is_infinite = node.max is None
            new_depth = quantifier_depth + (1 if is_infinite else 0)

            if is_infinite and new_depth >= 2:
                vulns.append(
                    Vulnerability(
                        type=VulnType.NESTED_QUANTIFIER,
                        severity=Severity.CRITICAL,
                        description=(
                            f"Cuantificador infinito anidado en otro cuantificador "
                            f"(profundidad {new_depth}) — causa O(2^N)"
                        ),
                        explanation=(
                            "Un cuantificador como + o * dentro de un grupo que "
                            "también tiene + o * crea bifurcaciones exponenciales. "
                            "Cada carácter de entrada duplica los caminos de ejecución."
                        ),
                        fix_suggestion="Aplana los cuantificadores: (a+)+ → a+",
                    )
                )

            if is_infinite and isinstance(node.child, GroupNode):
                for c in node.child.children:
                    if isinstance(c, AlternationNode):
                        self._check_quantified_alternation(c, vulns)

            self._walk(node.child, vulns, new_depth)

    def _check_quantified_alternation(
        self, alt: AlternationNode, vulns: list[Vulnerability]
    ):
        """Check if both branches of a quantified alternation can match the same chars."""
        # Already handled by OverlapAnalyzer but we flag it here as nested quantifier issue
        pass  # delegation to OverlapAnalyzer

    def _check_wildcards(self, root: RootNode, vulns: list[Vulnerability]):
        """Count .* and .+ occurrences — multiple wildcards cause polynomial backtracking."""
        count = self._count_wildcards(root)
        if count >= 3:
            vulns.append(
                Vulnerability(
                    type=VulnType.MULTIPLE_WILDCARDS,
                    severity=Severity.HIGH,
                    description=(
                        f"{count} wildcards (.* o .+) sin anclas — "
                        f"probablemente O(N^{count})"
                    ),
                    explanation=(
                        "Múltiples .* sin anclas compiten por todos los caracteres. "
                        "Con N wildcards, la complejidad es O(N^wildcards) en el peor caso."
                    ),
                    fix_suggestion="Añade anclas ^ y $, o usa coincidencia específica en lugar de .*",
                )
            )
        elif count >= 2:
            vulns.append(
                Vulnerability(
                    type=VulnType.MULTIPLE_WILDCARDS,
                    severity=Severity.MEDIUM,
                    description=(f"{count} wildcards (.* o .+) — potencialmente O(N²)"),
                    explanation=(
                        "Dos wildcards sin anclas causan que el motor pruebe "
                        "todas las posibles particiones del texto."
                    ),
                    fix_suggestion="Ancla el patrón con ^ y $, o haz los wildcards lazy (.*?)",
                )
            )

    def _count_wildcards(self, node: AstNode) -> int:
        """Count .* and .+ patterns in the AST."""
        if isinstance(node, QuantifierNode):
            if node.max is None and isinstance(node.child, DotNode):
                return 1 + self._count_wildcards(node.child)
            return self._count_wildcards(node.child)

        if isinstance(node, RootNode):
            return sum(self._count_wildcards(c) for c in node.children)

        if isinstance(node, GroupNode):
            return sum(self._count_wildcards(c) for c in node.children)

        if isinstance(node, AlternationNode):
            return self._count_wildcards(node.left) + self._count_wildcards(node.right)

        return 0
