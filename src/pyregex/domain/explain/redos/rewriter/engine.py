"""Rewrite Engine — Applies safe transformation strategies to vulnerable patterns.

Takes the AST and list of vulnerabilities, applies the best rewrite
strategy for each vulnerability, and produces a safe regex string.
"""

from __future__ import annotations
import re
from typing import Optional

from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    GroupNode,
    QuantifierNode,
    AlternationNode,
)
from pyregex.domain.explain.redos.models import (
    Vulnerability,
    VulnType,
)
from pyregex.domain.explain.redos.rewriter.strategies import (
    ast_to_regex,
    flatten_nested_quantifier,
    make_lazy,
    add_anchors,
    RewriteResult,
)


class RewriteEngine:
    """Applies rewrite strategies to eliminate ReDoS vulnerabilities."""

    def rewrite(
        self, pattern: str, ast: RootNode, vulnerabilities: list[Vulnerability]
    ) -> Optional[RewriteResult]:
        """Attempt to rewrite a vulnerable pattern into a safe one.

        Returns None if no rewrite is possible.
        """
        if not vulnerabilities:
            return None

        # Try strategies in order of importance
        for vuln in sorted(vulnerabilities, key=lambda v: list(VulnType).index(v.type)):
            result = self._try_rewrite(pattern, ast, vuln)
            if result:
                # Verify the rewrite compiles
                try:
                    re.compile(result.rewritten)
                    return result
                except re.error:
                    continue

        return None

    def _try_rewrite(
        self, pattern: str, ast: RootNode, vuln: Vulnerability
    ) -> Optional[RewriteResult]:
        """Try one rewrite strategy based on vulnerability type."""

        if vuln.type == VulnType.NESTED_QUANTIFIER:
            return self._rewrite_nested(pattern, ast)

        if vuln.type == VulnType.ADJACENT_OVERLAP:
            return self._rewrite_adjacent(pattern, ast)

        if vuln.type == VulnType.MULTIPLE_WILDCARDS:
            rewritten = make_lazy(pattern)
            if rewritten != pattern:
                return RewriteResult(
                    original=pattern,
                    rewritten=rewritten,
                    strategy="lazy_conversion",
                    explanation="Wildcards greedy convertidos a lazy para reducir backtracking",
                )
            return None

        if vuln.type in (
            VulnType.ALTERNATION_OVERLAP,
            VulnType.QUANTIFIER_SUFFIX_OVERLAP,
        ):
            # For these, suggest anchoring as the simplest fix
            rewritten = add_anchors(pattern)
            if rewritten != pattern:
                return RewriteResult(
                    original=pattern,
                    rewritten=rewritten,
                    strategy="anchor_addition",
                    explanation="Anclas ^ y $ añadidas para limitar las posiciones de inicio",
                )
            return None

        return None

    def _rewrite_nested(self, pattern: str, ast: RootNode) -> Optional[RewriteResult]:
        """Flatten nested quantifiers."""
        result = self._find_and_flatten(ast)
        if result:
            rewritten = ast_to_regex(ast)
            # Fallback: if AST roundtrip fails, do regex-level rewrite
            try:
                re.compile(rewritten)
            except re.error:
                rewritten = self._flatten_regex(pattern)

            if rewritten and rewritten != pattern:
                return RewriteResult(
                    original=pattern,
                    rewritten=rewritten,
                    strategy="nested_flatten",
                    explanation="Cuantificador anidado aplanado para eliminar backtracking exponencial",
                )
        # Regex-level fallback
        rewritten = self._flatten_regex(pattern)
        if rewritten and rewritten != pattern:
            return RewriteResult(
                original=pattern,
                rewritten=rewritten,
                strategy="nested_flatten",
                explanation="Cuantificador anidado aplanado para eliminar backtracking exponencial",
            )
        return None

    def _rewrite_adjacent(self, pattern: str, ast: RootNode) -> Optional[RewriteResult]:
        """Merge adjacent quantifiers."""
        rewritten = self._merge_regex(pattern)
        if rewritten and rewritten != pattern:
            return RewriteResult(
                original=pattern,
                rewritten=rewritten,
                strategy="adjacent_merge",
                explanation="Cuantificadores adyacentes fusionados para eliminar competencia",
            )
        return None

    def _find_and_flatten(self, node: AstNode) -> bool:
        """Walk AST and apply flatten_nested_quantifier in-place."""
        if isinstance(node, QuantifierNode):
            result = flatten_nested_quantifier(node)
            if result:
                return True
            return self._find_and_flatten(node.child)

        if isinstance(node, RootNode):
            for child in node.children:
                if self._find_and_flatten(child):
                    return True

        if isinstance(node, GroupNode):
            for child in node.children:
                if self._find_and_flatten(child):
                    return True

        if isinstance(node, AlternationNode):
            return self._find_and_flatten(node.left) or self._find_and_flatten(
                node.right
            )

        return False

    @staticmethod
    def _flatten_regex(pattern: str) -> Optional[str]:
        """Regex-level flattening: (a+)+ → a+, (a*)+ → a*, etc."""
        import re as _re

        # Pattern: (X+)+ or (X+)* or (X*)+ or (X*)*
        flattened = _re.sub(
            r"\(([^()]+)([+*])\)\s*([+*])",
            lambda m: (
                f"{m.group(1)}{'+' if m.group(2) == '+' and m.group(3) == '+' else '*'}"
            ),
            pattern,
        )
        return flattened if flattened != pattern else None

    @staticmethod
    def _merge_regex(pattern: str) -> Optional[str]:
        """Regex-level merging: \\w+\\w+ → \\w{2,}"""
        import re as _re

        # Merge identical quantified expressions
        merged = _re.sub(r"(\\[dDwWsS]|\[.*?\]|\.)(\+)\1(\+)", r"\g<1>{2,}", pattern)
        merged = _re.sub(r"(\\[dDwWsS]|\[.*?\]|\.)(\*)\1(\+)", r"\g<1>+", merged)
        merged = _re.sub(r"(\\[dDwWsS]|\[.*?\]|\.)(\+)\1(\*)", r"\g<1>+", merged)
        return merged if merged != pattern else None
