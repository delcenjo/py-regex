from __future__ import annotations
from typing import List
from pyregex.domain.explain.ast.nodes import (
    RootNode,
    LiteralNode,
    CharClassNode,
    SpecialCharNode,
    QuantifierNode,
    AnchorNode,
)


class PatternRecognizer:
    """Detects high-level semantic patterns (Hashes, Dates, etc.) from AST structures."""

    def recognize(self, root: RootNode) -> List[str]:
        """Returns a list of recognized pattern tags."""
        tags = []
        if self._is_md5_hash(root):
            tags.append("MD5 Hash")
        if self._is_uuid(root):
            tags.append("UUID")
        if self._is_iso_date(root):
            tags.append("ISO Date")
        return tags

    def _is_md5_hash(self, root: RootNode) -> bool:
        """Looks for \b[a-fA-F0-9]{32}\b or ^[a-fA-F0-9]{32}$"""
        children = root.children
        if len(children) != 3:
            return False

        # Check boundaries
        first, middle, last = children[0], children[1], children[2]

        has_boundaries = (
            isinstance(first, AnchorNode)
            and first.type_ == r"\b"
            and isinstance(last, AnchorNode)
            and last.type_ == r"\b"
        ) or (
            isinstance(first, AnchorNode)
            and first.type_ == "^"
            and isinstance(last, AnchorNode)
            and last.type_ == "$"
        )
        if not has_boundaries:
            return False

        # Check [a-fA-F0-9]{32}
        if (
            not isinstance(middle, QuantifierNode)
            or middle.min_cnt != 32
            or middle.max_cnt != 32
        ):
            return False

        child = middle.child
        if isinstance(child, CharClassNode):
            chars = (
                child.chars.replace("a-f", "")
                .replace("A-F", "")
                .replace("0-9", "")
                .replace("A-Fa-f", "")
            )
            # If it only contains valid hex ranges
            if not chars and not child.negated:
                return True

        return False

    def _is_uuid(self, root: RootNode) -> bool:
        """Simplified UUID check"""
        # Complex to write exact AST matcher for UUID quickly, return False for now
        return False

    def _is_iso_date(self, root: RootNode) -> bool:
        r"""Looks for \d{4}-\d{2}-\d{2}"""
        # \d{4}-\d{2}-\d{2} means: Quantifier(\d, 4), Literal('-'), Quantifier(\d, 2), Literal('-'), Quantifier(\d, 2)
        children = root.children

        # Strip anchors if present
        if children and isinstance(children[0], AnchorNode):
            children = children[1:]
        if children and isinstance(children[-1], AnchorNode):
            children = children[:-1]

        if len(children) != 5:
            return False

        c1, c2, c3, c4, c5 = children

        def is_d_quant(node, cnt):
            if (
                isinstance(node, QuantifierNode)
                and node.min_cnt == cnt
                and node.max_cnt == cnt
            ):
                inner = node.child
                return isinstance(inner, SpecialCharNode) and inner.char == r"\d"
            return False

        def is_hyphen(node):
            return isinstance(node, LiteralNode) and node.value == "-"

        if (
            is_d_quant(c1, 4)
            and is_hyphen(c2)
            and is_d_quant(c3, 2)
            and is_hyphen(c4)
            and is_d_quant(c5, 2)
        ):
            return True

        return False
