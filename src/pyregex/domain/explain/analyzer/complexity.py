from __future__ import annotations
from typing import List, Tuple
from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    GroupNode,
    QuantifierNode,
    AlternationNode,
)


class ComplexityAnalyzer:
    """Calculates Big-O complexity and ReDoS vulnerabilities from an AST."""

    def __init__(self, root: RootNode):
        self.root = root

    def analyze(self) -> Tuple[str, List[str]]:
        """Returns the Big-O complexity estimation and a list of warnings."""
        warnings = []
        has_exponential = self._detect_exponential_backtracking(self.root, 0)

        if has_exponential:
            warnings.append(
                "CRITICAL: Detectado posible ReDoS (Retroceso Catastrófico). Evita anidar cuantificadores iterativos (* o +) dentro de otros grupos iterativos."
            )
            return "O(2^N)", warnings

        warnings.extend(self._find_ambiguous_alternations(self.root))

        return "O(N)", warnings

    def _detect_exponential_backtracking(
        self, node: AstNode, quantifier_depth: int
    ) -> bool:
        """Heuristic: If we have an infinite quantifier inside an infinite quantifier, it's O(2^N)."""
        if isinstance(node, RootNode):
            for child in node.children:
                if self._detect_exponential_backtracking(child, quantifier_depth):
                    return True

        if isinstance(node, GroupNode):
            for child in node.children:
                if self._detect_exponential_backtracking(child, quantifier_depth):
                    return True

        if isinstance(node, AlternationNode):
            if self._detect_exponential_backtracking(node.left, quantifier_depth):
                return True
            if self._detect_exponential_backtracking(node.right, quantifier_depth):
                return True

        if isinstance(node, QuantifierNode):
            is_infinite = node.max is None and node.greedy
            if is_infinite:
                quantifier_depth += 1
                if quantifier_depth > 1:
                    # e.g., (a+)+
                    return True
            if self._detect_exponential_backtracking(node.child, quantifier_depth):
                return True

        return False

    def _find_ambiguous_alternations(self, node: AstNode) -> List[str]:
        return []
