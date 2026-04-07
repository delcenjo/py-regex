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


class HumanTranslator(ASTVisitor):
    """Converts normalized AST nodes into human language."""

    def __init__(self, mode: str = "simple"):
        self.mode = mode  # 'simple', 'detailed', 'expert'
        self.output: List[str] = []
        self._indent = 0

    def translate(self, root: RootNode) -> str:
        self.output = []
        self._indent = 0
        root.accept(self)
        return "\n".join(self.output)

    def _indent_str(self) -> str:
        return "  " * self._indent

    def _add_line(self, text: str):
        self.output.append(self._indent_str() + text)

    def visit_literal(self, node: LiteralNode) -> Any:
        self._add_line(f"- Literal characters: '{node.value}'")

    def visit_dot(self, node: DotNode) -> Any:
        self._add_line("- Any single character (except newline)")

    def visit_char_class(self, node: CharClassNode) -> Any:
        prefix = "NOT " if node.negated else ""
        self._add_line(f"- Any single character {prefix}in set: [{node.chars}]")

    def visit_special_char(self, node: SpecialCharNode) -> Any:
        meaning = node.char
        if node.char == r"\d":
            meaning = "digit (0-9)"
        elif node.char == r"\D":
            meaning = "non-digit"
        elif node.char == r"\w":
            meaning = "word character (a-z, A-Z, 0-9, _)"
        elif node.char == r"\W":
            meaning = "non-word character"
        elif node.char == r"\s":
            meaning = "whitespace character"
        elif node.char == r"\S":
            meaning = "non-whitespace character"
        elif node.char == r"letters":
            meaning = "letter (a-z, A-Z)"
        self._add_line(f"- A {meaning}")

    def visit_anchor(self, node: AnchorNode) -> Any:
        meaning = node.type_
        if node.type_ == "^":
            meaning = "start of string/line"
        elif node.type_ == "$":
            meaning = "end of string/line"
        elif node.type_ == r"\b":
            meaning = "word boundary"
        elif node.type_ == r"\B":
            meaning = "non-word boundary"
        self._add_line(f"- Matches exactly at the {meaning}")

    def visit_quantifier(self, node: QuantifierNode) -> Any:
        greed = " (greedy)" if node.greedy else " (lazy)"
        if node.min_cnt == 0 and node.max_cnt is None:
            desc = f"Matched 0 or more times{greed}"
        elif node.min_cnt == 1 and node.max_cnt is None:
            desc = f"Matched 1 or more times{greed}"
        elif node.min_cnt == 0 and node.max_cnt == 1:
            desc = f"Optionally matched (0 or 1 time){greed}"
        elif node.min_cnt == node.max_cnt:
            desc = f"Matched exactly {node.min_cnt} times{greed}"
        else:
            max_str = str(node.max_cnt) if node.max_cnt is not None else "infinity"
            desc = f"Matched between {node.min_cnt} and {max_str} times{greed}"

        self._add_line(f"- {desc}:")
        self._indent += 1
        node.child.accept(self)
        self._indent -= 1

    def visit_group(self, node: GroupNode) -> Any:
        if node.is_capture:
            name_str = f" named '{node.name}'" if node.name else ""
            self._add_line(f"- Capture Group{name_str} containing:")
        else:
            if node.name == "lookahead":
                self._add_line("- Must be followed by (Lookahead):")
            elif node.name == "lookbehind":
                self._add_line("- Must be preceded by (Lookbehind):")
            else:
                self._add_line("- Group containing:")

        self._indent += 1
        for child in node.children:
            child.accept(self)
        self._indent -= 1

    def visit_alternation(self, node: AlternationNode) -> Any:
        self._add_line("- Match EITHER:")
        self._indent += 1
        node.left.accept(self)
        self._indent -= 1
        self._add_line("- OR:")
        self._indent += 1
        node.right.accept(self)
        self._indent -= 1

    def visit_root(self, node: RootNode) -> Any:
        if self.mode != "simple":
            self._add_line("Pattern Breakdown:")
        for child in node.children:
            child.accept(self)
