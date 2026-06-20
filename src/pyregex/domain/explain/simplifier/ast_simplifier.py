from __future__ import annotations
from typing import Any
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


class ASTSimplifier(ASTVisitor):
    """Simplifies AST structures before translation."""

    def simplify(self, root: RootNode) -> RootNode:
        root.accept(self)
        return root

    def visit_literal(self, node: LiteralNode) -> Any:
        return node

    def visit_dot(self, node: DotNode) -> Any:
        return node

    def visit_char_class(self, node: CharClassNode) -> Any:
        if not node.negated:
            if node.chars == "0-9":
                return SpecialCharNode(r"\d")
            if node.chars in ("a-zA-Z", "A-Za-z"):
                return SpecialCharNode(r"letters")  # custom pseudo-special
        return node

    def visit_special_char(self, node: SpecialCharNode) -> Any:
        return node

    def visit_anchor(self, node: AnchorNode) -> Any:
        return node

    def visit_quantifier(self, node: QuantifierNode) -> Any:
        node.child = node.child.accept(self)
        return node

    def visit_group(self, node: GroupNode) -> Any:
        new_children = []
        for child in node.children:
            new_child = child.accept(self)
            new_children.append(new_child)
        node.children = new_children

        # Unwrap a non-capturing group with a single atomic child (safe to elide).
        if not node.is_capture and node.name is None and len(node.children) == 1:
            child = node.children[0]
            if isinstance(
                child, (LiteralNode, SpecialCharNode, CharClassNode, DotNode)
            ):
                return child

        return node

    def visit_alternation(self, node: AlternationNode) -> Any:
        node.left = node.left.accept(self)
        node.right = node.right.accept(self)
        return node

    def visit_root(self, node: RootNode) -> Any:
        new_children = []
        for child in node.children:
            new_children.append(child.accept(self))
        node.children = new_children
        return node
