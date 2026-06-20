# src/pyregex/domain/explain/models/ast.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class AstNode:
    """Base node for all structural Regex elements in the Abstract Syntax Tree."""

    pass


@dataclass
class RootNode(AstNode):
    """The root of the Regex AST."""

    children: List[AstNode] = field(default_factory=list)


@dataclass
class LiteralNode(AstNode):
    """Represents one or more literal characters to match exactly."""

    value: str


@dataclass
class DotNode(AstNode):
    """Represents the . wildcard."""

    matches_newline: bool = False


@dataclass
class AnchorNode(AstNode):
    """Represents boundary anchors like ^, $, \\b."""

    type: str  # 'start', 'end', 'word_boundary', 'non_word_boundary'
    value: str


@dataclass
class CharClassNode(AstNode):
    """Represents character categories like \\d, \\w, \\s and their negations."""

    type: str  # 'digit', 'word', 'whitespace'
    negated: bool
    value: str


@dataclass
class AlternationNode(AstNode):
    """Represents the | OR operator."""

    left: AstNode
    right: AstNode


@dataclass
class SetClassNode(AstNode):
    """Represents a character set like [a-zA-Z0-9] or [^\\d]."""

    negated: bool
    items: List[AstNode] = field(
        default_factory=list
    )  # Contains LiteralNode or RangeNode


@dataclass
class RangeNode(AstNode):
    """Represents a range inside a SetClassNode (e.g., a-z)."""

    start: str
    end: str


@dataclass
class GroupNode(AstNode):
    """Represents a capturing or non-capturing block."""

    type: str  # 'capture', 'non_capture', 'lookahead', 'lookbehind', 'negative_lookahead', 'negative_lookbehind'
    name: Optional[str] = None
    children: List[AstNode] = field(default_factory=list)


@dataclass
class QuantifierNode(AstNode):
    """Represents repetition constraints wrapping a child node."""

    min: int
    max: Optional[int]  # None means infinite
    greedy: bool = True
    child: AstNode = field(default=None)  # type: ignore


@dataclass
class BackreferenceNode(AstNode):
    """Represents a reference to a previously captured group."""

    ref_id: str  # Can be an integer string '1' or a group name 'mygroup'


@dataclass
class FlagNode(AstNode):
    """Represents an inline flag toggle like (?i)."""

    flags_added: str
    flags_removed: str
