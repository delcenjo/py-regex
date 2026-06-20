from __future__ import annotations
from typing import List, Any
from pyregex.domain.explain.ast.nodes import (
    RootNode,
    LiteralNode,
    DotNode,
    CharClassNode,
    SpecialCharNode,
    AnchorNode,
    QuantifierNode,
    GroupNode,
    AlternationNode,
    ASTVisitor,
)


class WarningLinter(ASTVisitor):
    """Detects dangerous or inefficient regex patterns."""

    def __init__(self):
        self.warnings: List[str] = []
        self._in_greedy_quantifier = False

    def lint(self, root: RootNode) -> List[str]:
        self.warnings = []
        root.accept(self)
        return self.warnings

    def visit_literal(self, node: LiteralNode) -> Any:
        pass

    def visit_dot(self, node: DotNode) -> Any:
        if self._in_greedy_quantifier:
            self.warnings.append(
                "High potential for catastrophic backtracking (ReDoS) due to greedy .* or .+"
            )

    def visit_char_class(self, node: CharClassNode) -> Any:
        pass

    def visit_special_char(self, node: SpecialCharNode) -> Any:
        pass

    def visit_anchor(self, node: AnchorNode) -> Any:
        pass

    def visit_quantifier(self, node: QuantifierNode) -> Any:
        # Detect Nested Quantifiers (e.g. (a+)+)
        if isinstance(node.child, GroupNode):
            for inner in node.child.children:
                if isinstance(inner, QuantifierNode) and node.greedy and inner.greedy:
                    self.warnings.append(
                        "Nested greedy quantifiers detected. Extremely high risk of ReDoS."
                    )
                    break

        # Check child safely
        prev_greedy = self._in_greedy_quantifier
        if node.greedy and node.max_cnt is None:
            self._in_greedy_quantifier = True

        node.child.accept(self)

        self._in_greedy_quantifier = prev_greedy

    def visit_group(self, node: GroupNode) -> Any:
        if (
            node.is_capture
            and len(node.children) == 1
            and isinstance(node.children[0], LiteralNode)
        ):
            self.warnings.append(
                "Useless capture group covering a static literal string."
            )

        for child in node.children:
            child.accept(self)

    def visit_alternation(self, node: AlternationNode) -> Any:
        node.left.accept(self)
        node.right.accept(self)

    def visit_root(self, node: RootNode) -> Any:
        for child in node.children:
            child.accept(self)
