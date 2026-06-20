from __future__ import annotations
from typing import List, Dict
from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    GroupNode,
    LiteralNode,
    QuantifierNode,
    AlternationNode,
)


class AstLinter:
    """Checks the AST for redundant semantics and suggests optimizations."""

    def __init__(self, root: RootNode):
        self.root = root

    def lint(self) -> List[Dict[str, str]]:
        """Returns a list of linting suggestions."""
        self.suggestions = []
        self._walk(self.root)
        return self.suggestions

    def _walk(self, node: AstNode):
        if isinstance(node, RootNode):
            for child in node.children:
                self._walk(child)

        elif isinstance(node, GroupNode):
            if (
                node.type == "non_capture"
                and len(node.children) == 1
                and isinstance(node.children[0], LiteralNode)
            ):
                self.suggestions.append(
                    {
                        "type": "optimization",
                        "message": f"El grupo sin captura (?:{node.children[0].value}) contiene solo un literal constante y no parece estar cuantificado. Puedes eliminar los paréntesis.",
                    }
                )
            for child in node.children:
                self._walk(child)

        elif isinstance(node, AlternationNode):
            if isinstance(node.left, LiteralNode) and isinstance(
                node.right, LiteralNode
            ):
                if node.left.value == node.right.value:
                    self.suggestions.append(
                        {
                            "type": "redundancy",
                            "message": f"Alternancia redundante '{node.left.value}|{node.right.value}'. Puedes simplificarla.",
                        }
                    )
            self._walk(node.left)
            self._walk(node.right)

        elif isinstance(node, QuantifierNode):
            # Check useless ??
            if (
                getattr(node.child, "type", None) == "capture"
                and node.min == 0
                and node.max == 1
                and not node.greedy
            ):
                pass  # This is fine
            self._walk(node.child)
