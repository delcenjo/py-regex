from __future__ import annotations
from typing import Dict, Any
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


class SemanticAnalyzer(ASTVisitor):
    """Interprets the AST to extract high-level metrics and context."""

    def __init__(self):
        self.max_depth = 0
        self.current_depth = 0
        self.node_count = 0
        self.has_captures = False
        self.has_lookarounds = False

    def analyze(self, root: RootNode) -> Dict[str, Any]:
        self.max_depth = 0
        self.current_depth = 0
        self.node_count = 0
        self.has_captures = False
        self.has_lookarounds = False

        root.accept(self)

        return {
            "max_depth": self.max_depth,
            "node_count": self.node_count,
            "has_captures": self.has_captures,
            "has_lookarounds": self.has_lookarounds,
            "complexity_score": self._calculate_complexity(),
        }

    def _calculate_complexity(self) -> int:
        score = self.node_count + (self.max_depth * 2)
        if self.has_lookarounds:
            score += 5
        return score

    def _enter_node(self):
        self.node_count += 1
        self.current_depth += 1
        if self.current_depth > self.max_depth:
            self.max_depth = self.current_depth

    def _exit_node(self):
        self.current_depth -= 1

    def visit_literal(self, node: LiteralNode) -> Any:
        self._enter_node()
        self._exit_node()

    def visit_dot(self, node: DotNode) -> Any:
        self._enter_node()
        self._exit_node()

    def visit_char_class(self, node: CharClassNode) -> Any:
        self._enter_node()
        self._exit_node()

    def visit_special_char(self, node: SpecialCharNode) -> Any:
        self._enter_node()
        self._exit_node()

    def visit_anchor(self, node: AnchorNode) -> Any:
        self._enter_node()
        self._exit_node()

    def visit_quantifier(self, node: QuantifierNode) -> Any:
        self._enter_node()
        node.child.accept(self)
        self._exit_node()

    def visit_group(self, node: GroupNode) -> Any:
        self._enter_node()
        if node.is_capture:
            self.has_captures = True
        if node.name in ("lookahead", "lookbehind"):
            self.has_lookarounds = True

        for child in node.children:
            child.accept(self)
        self._exit_node()

    def visit_alternation(self, node: AlternationNode) -> Any:
        self._enter_node()
        node.left.accept(self)
        node.right.accept(self)
        self._exit_node()

    def visit_root(self, node: RootNode) -> Any:
        self._enter_node()
        for child in node.children:
            child.accept(self)
        self._exit_node()
