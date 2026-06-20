"""Rewrite Strategies — Safe transformations for vulnerable patterns.

Each strategy takes an AST node and vulnerability, and returns a
safe replacement pattern string (or None if not applicable).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    LiteralNode,
    DotNode,
    CharClassNode,
    SetClassNode,
    RangeNode,
    AlternationNode,
    GroupNode,
    QuantifierNode,
    AnchorNode,
    BackreferenceNode,
    FlagNode,
)


@dataclass
class RewriteResult:
    """Result of applying a rewrite strategy."""

    original: str
    rewritten: str
    strategy: str
    explanation: str


def ast_to_regex(node: AstNode) -> str:
    """Regenerate regex string from AST node."""
    if isinstance(node, RootNode):
        return "".join(ast_to_regex(c) for c in node.children)

    if isinstance(node, LiteralNode):
        specials = r"\.^$*+?{}[]|()"
        result = []
        for ch in node.value:
            if ch in specials:
                result.append("\\" + ch)
            else:
                result.append(ch)
        return "".join(result)

    if isinstance(node, DotNode):
        return "."

    if isinstance(node, AnchorNode):
        return node.value

    if isinstance(node, CharClassNode):
        return node.value

    if isinstance(node, SetClassNode):
        parts = []
        for item in node.items:
            if isinstance(item, LiteralNode):
                parts.append(item.value)
            elif isinstance(item, RangeNode):
                parts.append(f"{item.start}-{item.end}")
            elif isinstance(item, CharClassNode):
                parts.append(item.value)
        prefix = "[^" if node.negated else "["
        return f"{prefix}{''.join(parts)}]"

    if isinstance(node, AlternationNode):
        return f"{ast_to_regex(node.left)}|{ast_to_regex(node.right)}"

    if isinstance(node, GroupNode):
        inner = "".join(ast_to_regex(c) for c in node.children)
        if node.type == "non_capture":
            return f"(?:{inner})"
        if node.type == "lookahead":
            return f"(?={inner})"
        if node.type == "negative_lookahead":
            return f"(?!{inner})"
        if node.type == "lookbehind":
            return f"(?<={inner})"
        if node.type == "negative_lookbehind":
            return f"(?<!{inner})"
        if node.name:
            return f"(?P<{node.name}>{inner})"
        return f"({inner})"

    if isinstance(node, QuantifierNode):
        child = ast_to_regex(node.child)
        lazy = "" if node.greedy else "?"
        if node.min == 0 and node.max is None:
            return f"{child}*{lazy}"
        if node.min == 1 and node.max is None:
            return f"{child}+{lazy}"
        if node.min == 0 and node.max == 1:
            return f"{child}?{lazy}"
        if node.max is None:
            return f"{child}{{{node.min},}}{lazy}"
        if node.min == node.max:
            return f"{child}{{{node.min}}}{lazy}"
        return f"{child}{{{node.min},{node.max}}}{lazy}"

    if isinstance(node, BackreferenceNode):
        return f"\\{node.ref_id}"

    if isinstance(node, FlagNode):
        return f"(?{node.flags_added})"

    return ""


def flatten_nested_quantifier(node: QuantifierNode) -> Optional[str]:
    """(a+)+ → a+  |  (a*)+ → a*  |  (a+)* → a*

    Applies when a quantifier wraps a group containing only a single
    quantified element.
    """
    if not isinstance(node.child, GroupNode):
        return None

    group = node.child
    if len(group.children) != 1:
        return None

    inner = group.children[0]
    if not isinstance(inner, QuantifierNode):
        return None

    if node.max is not None or inner.max is not None:
        return None

    child_str = ast_to_regex(inner.child)

    if node.min == 0 or inner.min == 0:
        return f"{child_str}*"
    else:
        return f"{child_str}+"


def merge_adjacent_quantifiers(q1: QuantifierNode, q2: QuantifierNode) -> Optional[str]:
    """\\w+\\w+ → \\w{2,}  |  \\d*\\d+ → \\d+

    Merges two adjacent quantifiers over the same char set.
    """
    cs1 = ast_to_regex(q1.child)
    cs2 = ast_to_regex(q2.child)

    if cs1 != cs2:
        return None

    min_total = q1.min + q2.min
    max_total: Optional[int] = None

    if q1.max is None or q2.max is None:
        max_total = None
    else:
        max_total = q1.max + q2.max

    if max_total is None:
        if min_total <= 1:
            return f"{cs1}+"
        return f"{cs1}{{{min_total},}}"
    elif min_total == max_total:
        return f"{cs1}{{{min_total}}}"
    else:
        return f"{cs1}{{{min_total},{max_total}}}"


def make_lazy(pattern: str) -> str:
    """Convert greedy quantifiers to lazy: .* → .*?"""
    import re

    return re.sub(r"([*+])(?!\?)", r"\1?", pattern)


def add_anchors(pattern: str) -> str:
    """Add ^ and $ if not present."""
    if not pattern.startswith("^"):
        pattern = "^" + pattern
    if not pattern.endswith("$"):
        pattern = pattern + "$"
    return pattern
