# src/pyregex/domain/explain/formatters/tree.py
from __future__ import annotations
from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    LiteralNode,
    DotNode,
    AnchorNode,
    CharClassNode,
    AlternationNode,
    SetClassNode,
    RangeNode,
    GroupNode,
    QuantifierNode,
    BackreferenceNode,
    FlagNode,
)


class TreeFormatter:
    """Generates an ASCII standard tree structure from a Regex AST."""

    def __init__(self, root: RootNode):
        self.root = root

    def format(self) -> str:
        """Returns the complete ASCII tree as a string."""
        lines = ["REGEX PATTERN"]
        for i, child in enumerate(self.root.children):
            is_last = i == len(self.root.children) - 1
            self._walk(child, prefix="", is_last=is_last, lines=lines)
        return "\n".join(lines)

    def _walk(self, node: AstNode, prefix: str, is_last: bool, lines: list[str]):
        connector = "└── " if is_last else "├── "
        child_prefix = prefix + ("    " if is_last else "│   ")

        label = self._get_node_label(node)
        lines.append(f"{prefix}{connector}{label}")

        children = self._get_children(node)
        for i, child in enumerate(children):
            self._walk(child, child_prefix, i == len(children) - 1, lines)

    def _get_node_label(self, node: AstNode) -> str:
        if isinstance(node, LiteralNode):
            return f"Literal: '{node.value}'"
        if isinstance(node, DotNode):
            return "Wildcard (.)"
        if isinstance(node, AnchorNode):
            if node.type == "start":
                return "Start of String (^)"
            if node.type == "end":
                return "End of String ($)"
            return f"Word Boundary ({node.value})"
        if isinstance(node, QuantifierNode):
            target = f"[{node.min}, {node.max if node.max is not None else '∞'}]"
            return f"Quantifier {target} ({'Greedy' if node.greedy else 'Lazy'})"
        if isinstance(node, GroupNode):
            if node.type == "capture":
                return f"Group (Capture){' Name: ' + node.name if node.name else ''}"
            return f"Group ({node.type.replace('_', ' ').title()})"
        if isinstance(node, AlternationNode):
            return "Alternation (OR)"
        if isinstance(node, SetClassNode):
            return f"Character Set {'(Negated)' if node.negated else ''}"
        if isinstance(node, CharClassNode):
            return f"Class: {node.type.title()} {'(Negated)' if node.negated else ''}"
        if isinstance(node, RangeNode):
            return f"Range: {node.start}-{node.end}"
        if isinstance(node, BackreferenceNode):
            return f"Backreference -> \\{node.ref_id}"
        if isinstance(node, FlagNode):
            return f"Flags: (?{node.flags_added})"
        return type(node).__name__

    def _get_children(self, node: AstNode) -> list[AstNode]:
        if isinstance(node, GroupNode) or isinstance(node, RootNode):
            return node.children
        if isinstance(node, QuantifierNode):
            return [node.child] if node.child else []
        if isinstance(node, AlternationNode):
            return [node.left, node.right]
        if isinstance(node, SetClassNode):
            return node.items
        return []
