"""Sentinel Engine — AST-Based Regex Coverage Tracker.

Calculates which parts of a regex (alternation branches, quantifiers)
were actually exercised by the provided input texts.
"""

from __future__ import annotations
import re
from typing import Set

from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    AlternationNode,
    QuantifierNode,
    GroupNode,
)
from pyregex.domain.sentinel.models import CoverageReport
from pyregex.domain.explain.redos.rewriter.strategies import ast_to_regex


class CoverageTracker:
    """Tracks branch and quantifier coverage within a regex AST."""

    def __init__(self, root: RootNode):
        self.root = root
        self._total_branches: list[str] = []
        self._total_quantifiers: list[str] = []
        self._covered_branches: Set[str] = set()
        self._covered_quantifiers: Set[str] = set()

        # Pre-calculate total branches and quantifiers
        self._discover_nodes(self.root)

    def process_match(self, text: str, span: tuple[int, int]) -> None:
        """Analyze a successful match to see which branches it exercised.

        Heuristic: For each alternation node A|B, we check if the matched
        substring satisfies A, B, or both. We mark those as covered.
        """
        matched_substr = text[span[0] : span[1]]

        for pattern in self._total_branches:
            if pattern not in self._covered_branches:
                try:
                    if re.search(pattern, matched_substr):
                        self._covered_branches.add(pattern)
                except re.error:
                    pass

        for pattern in self._total_quantifiers:
            if pattern not in self._covered_quantifiers:
                try:
                    if len(re.findall(pattern, matched_substr)) > 0:
                        self._covered_quantifiers.add(pattern)
                except re.error:
                    pass

    def generate_report(self) -> CoverageReport:
        """Produce the final AST coverage report."""
        missed_branches = [
            b for b in self._total_branches if b not in self._covered_branches
        ]
        missed_quantifiers = [
            q for q in self._total_quantifiers if q not in self._covered_quantifiers
        ]

        return CoverageReport(
            total_branches=len(self._total_branches),
            covered_branches=len(self._covered_branches),
            total_quantifiers=len(self._total_quantifiers),
            covered_quantifiers=len(self._covered_quantifiers),
            missed_alternations=missed_branches,
            missed_quantifiers=missed_quantifiers,
        )

    def _discover_nodes(self, node: AstNode) -> None:
        """Walk the AST to discover all targetable nodes."""
        if isinstance(node, RootNode):
            for child in node.children:
                self._discover_nodes(child)

        elif isinstance(node, GroupNode):
            for child in node.children:
                self._discover_nodes(child)

        elif isinstance(node, AlternationNode):
            left_str = ast_to_regex(node.left)
            right_str = ast_to_regex(node.right)
            if left_str:
                self._total_branches.append(left_str)
            if right_str:
                self._total_branches.append(right_str)

            self._discover_nodes(node.left)
            self._discover_nodes(node.right)

        elif isinstance(node, QuantifierNode):
            q_str = ast_to_regex(node)
            if q_str:
                self._total_quantifiers.append(q_str)
            self._discover_nodes(node.child)
