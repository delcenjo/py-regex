from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, Any


class Node(ABC):
    """Base AST Node for a regex component."""

    @abstractmethod
    def accept(self, visitor: "ASTVisitor") -> Any:
        pass

    def __repr__(self) -> str:
        return self.__class__.__name__


class LiteralNode(Node):
    def __init__(self, value: str):
        self.value = value

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_literal(self)

    def __repr__(self) -> str:
        return f"Literal('{self.value}')"


class DotNode(Node):
    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_dot(self)


class CharClassNode(Node):
    def __init__(self, chars: str, negated: bool = False):
        self.chars = chars
        self.negated = negated

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_char_class(self)

    def __repr__(self) -> str:
        prefix = "^" if self.negated else ""
        return f"CharClass([{prefix}{self.chars}])"


class SpecialCharNode(Node):
    def __init__(self, char: str):
        self.char = char  # e.g., \d, \w, \s etc.

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_special_char(self)


class AnchorNode(Node):
    def __init__(self, type_: str):
        self.type_ = type_  # ^, $, \b, \B

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_anchor(self)

    def __repr__(self) -> str:
        return f"Anchor('{self.type_}')"


class QuantifierNode(Node):
    def __init__(
        self, child: Node, min_cnt: int, max_cnt: Optional[int], greedy: bool = True
    ):
        self.child = child
        self.min_cnt = min_cnt
        self.max_cnt = max_cnt  # None means infinity
        self.greedy = greedy

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_quantifier(self)


class GroupNode(Node):
    def __init__(
        self, children: List[Node], is_capture: bool = True, name: Optional[str] = None
    ):
        self.children = children
        self.is_capture = is_capture
        self.name = name

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_group(self)


class AlternationNode(Node):
    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_alternation(self)


class RootNode(Node):
    def __init__(self, children: List[Node]):
        self.children = children

    def accept(self, visitor: "ASTVisitor") -> Any:
        return visitor.visit_root(self)


class ASTVisitor(ABC):
    """Visitor Interface for traversing the AST."""

    @abstractmethod
    def visit_literal(self, node: LiteralNode) -> Any:
        pass

    @abstractmethod
    def visit_dot(self, node: DotNode) -> Any:
        pass

    @abstractmethod
    def visit_char_class(self, node: CharClassNode) -> Any:
        pass

    @abstractmethod
    def visit_special_char(self, node: SpecialCharNode) -> Any:
        pass

    @abstractmethod
    def visit_anchor(self, node: AnchorNode) -> Any:
        pass

    @abstractmethod
    def visit_quantifier(self, node: QuantifierNode) -> Any:
        pass

    @abstractmethod
    def visit_group(self, node: GroupNode) -> Any:
        pass

    @abstractmethod
    def visit_alternation(self, node: AlternationNode) -> Any:
        pass

    @abstractmethod
    def visit_root(self, node: RootNode) -> Any:
        pass
