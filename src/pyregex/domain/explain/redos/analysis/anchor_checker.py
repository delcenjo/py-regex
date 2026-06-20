"""Anchor Checker — Verifies if regex is protected by anchors.

Anchored patterns (^...$) are generally safe from worst-case
backtracking because the engine can't try different start positions.
This module checks for anchor protection and adjusts severity.
"""

from __future__ import annotations

from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    AnchorNode,
    GroupNode,
    AlternationNode,
)
from pyregex.domain.explain.redos.models import Vulnerability, Severity


class AnchorChecker:
    """Checks if a regex pattern is protected by anchors."""

    def check(self, root: RootNode) -> tuple[bool, bool, bool]:
        """Returns (has_start_anchor, has_end_anchor, fully_anchored)."""
        has_start = self._has_start_anchor(root)
        has_end = self._has_end_anchor(root)
        return has_start, has_end, has_start and has_end

    def mitigate(
        self, vulns: list[Vulnerability], root: RootNode
    ) -> list[Vulnerability]:
        """Reduce severity of vulnerabilities if pattern is anchored."""
        has_start, has_end, fully = self.check(root)

        if not fully:
            return vulns

        # Full anchoring reduces severity by one level
        result = []
        for v in vulns:
            if v.severity == Severity.CRITICAL:
                # Nested quantifiers are STILL dangerous even with anchors
                # because the exponential branching happens at interior positions
                new_v = Vulnerability(
                    type=v.type,
                    severity=Severity.HIGH,
                    position=v.position,
                    span=v.span,
                    description=v.description + " (mitigado por anclas ^/$)",
                    explanation=v.explanation,
                    fix_suggestion=v.fix_suggestion,
                )
                result.append(new_v)
            elif v.severity == Severity.HIGH:
                new_v = Vulnerability(
                    type=v.type,
                    severity=Severity.MEDIUM,
                    position=v.position,
                    span=v.span,
                    description=v.description + " (mitigado por anclas ^/$)",
                    explanation=v.explanation,
                    fix_suggestion=v.fix_suggestion,
                )
                result.append(new_v)
            elif v.severity == Severity.MEDIUM:
                new_v = Vulnerability(
                    type=v.type,
                    severity=Severity.LOW,
                    position=v.position,
                    span=v.span,
                    description=v.description + " (mitigado por anclas ^/$)",
                    explanation=v.explanation,
                    fix_suggestion=v.fix_suggestion,
                )
                result.append(new_v)
            else:
                result.append(v)

        return result

    def _has_start_anchor(self, node: AstNode) -> bool:
        """Check if the first consumable position is anchored with ^ or \\A."""
        if isinstance(node, RootNode):
            if node.children:
                return self._has_start_anchor(node.children[0])
            return False

        if isinstance(node, AnchorNode):
            return node.type in ("start",)

        if isinstance(node, GroupNode):
            if node.children:
                return self._has_start_anchor(node.children[0])
            return False

        if isinstance(node, AlternationNode):
            return self._has_start_anchor(node.left) and self._has_start_anchor(
                node.right
            )

        return False

    def _has_end_anchor(self, node: AstNode) -> bool:
        """Check if the last position is anchored with $ or \\Z."""
        if isinstance(node, RootNode):
            if node.children:
                return self._has_end_anchor(node.children[-1])
            return False

        if isinstance(node, AnchorNode):
            return node.type in ("end",)

        if isinstance(node, GroupNode):
            if node.children:
                return self._has_end_anchor(node.children[-1])
            return False

        if isinstance(node, AlternationNode):
            return self._has_end_anchor(node.left) and self._has_end_anchor(node.right)

        return False
