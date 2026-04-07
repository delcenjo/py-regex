from __future__ import annotations
from typing import List, Optional
from pyregex.domain.explain.ast.nodes import (
    Node,
    RootNode,
    LiteralNode,
    DotNode,
    CharClassNode,
    SpecialCharNode,
    AnchorNode,
    QuantifierNode,
    GroupNode,
    AlternationNode,
)


class RegexParser:
    """Parses a regex string into an AST using recursive descent."""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0
        self.length = len(pattern)

    def parse(self) -> RootNode:
        children = self._parse_alternation()
        if self.pos < self.length:
            raise ValueError(
                f"Unexpected character at position {self.pos}: '{self.pattern[self.pos]}'"
            )
        return RootNode(
            [children] if isinstance(children, AlternationNode) else children
        )

    def _peek(self) -> Optional[str]:
        if self.pos < self.length:
            return self.pattern[self.pos]
        return None

    def _consume(self) -> str:
        char = self.pattern[self.pos]
        self.pos += 1
        return char

    def _parse_alternation(self) -> Node | List[Node]:
        nodes = self._parse_sequence()
        if self._peek() == "|":
            self._consume()  # Consume '|'
            right = self._parse_alternation()
            # Wrap nodes in GroupNode internally or just let Alternation take sequence
            left_node = (
                GroupNode(nodes, is_capture=False)
                if len(nodes) > 1
                else (nodes[0] if nodes else LiteralNode(""))
            )
            right_node = GroupNode(
                right if isinstance(right, list) else [right], is_capture=False
            )
            return AlternationNode(left_node, right_node)
        return nodes

    def _parse_sequence(self) -> List[Node]:
        nodes = []
        while self.pos < self.length:
            char = self._peek()
            if char in (")", "|"):
                break
            node = self._parse_atom()
            if node:
                nodes.append(node)
        return nodes

    def _parse_atom(self) -> Optional[Node]:
        char = self._consume()
        node: Node

        if char == ".":
            node = DotNode()
        elif char in ("^", "$"):
            node = AnchorNode(char)
        elif char == "\\":
            if self.pos >= self.length:
                node = LiteralNode("\\")
            else:
                next_char = self._consume()
                if next_char in ("b", "B", "A", "Z", "z"):
                    node = AnchorNode(f"\\{next_char}")
                elif next_char in ("d", "D", "w", "W", "s", "S"):
                    node = SpecialCharNode(f"\\{next_char}")
                else:
                    node = LiteralNode(next_char)
        elif char == "[":
            node = self._parse_char_class()
        elif char == "(":
            node = self._parse_group()
        elif char in ("*", "+", "?", "{"):
            # Not an atom, but could be a quantifier without preceding atom in bad regex. Treat as literal.
            node = LiteralNode(char)
        else:
            node = LiteralNode(char)

        # Parse potential quantifier for this atom
        return self._parse_quantifier(node)

    def _parse_char_class(self) -> CharClassNode:
        negated = False
        if self._peek() == "^":
            self._consume()
            negated = True

        chars = ""
        while self.pos < self.length:
            char = self._consume()
            if char == "]":
                break
            elif char == "\\":
                if self.pos < self.length:
                    chars += "\\" + self._consume()
            else:
                chars += char

        return CharClassNode(chars, negated)

    def _parse_group(self) -> GroupNode:
        is_capture = True
        name = None

        if self._peek() == "?":
            self._consume()  # Consume '?'
            modifier = self._peek()
            if modifier == ":":
                self._consume()
                is_capture = False
            elif modifier == "P":
                self._consume()
                if self._peek() == "<":
                    self._consume()
                    name = ""
                    while self.pos < self.length and self._peek() != ">":
                        name += self._consume()
                    if self._peek() == ">":
                        self._consume()
            elif modifier == "=" or modifier == "!":
                # Lookahead
                self._consume()
                is_capture = False
                name = "lookahead"
            elif modifier == "<":
                self._consume()
                if self._peek() in ("=", "!"):
                    self._consume()
                    is_capture = False
                    name = "lookbehind"

        inner_nodes = self._parse_alternation()
        if self._peek() == ")":
            self._consume()

        children = (
            [inner_nodes]
            if isinstance(inner_nodes, AlternationNode)
            else (inner_nodes if isinstance(inner_nodes, list) else [inner_nodes])
        )
        return GroupNode(children, is_capture, name)

    def _parse_quantifier(self, node: Node) -> Node:
        # Check if we have a quantifier character
        char = self._peek()
        if char not in ("*", "+", "?", "{"):
            return node

        min_cnt, max_cnt = 1, 1
        has_quantifier = False

        if char == "*":
            self._consume()
            min_cnt, max_cnt = 0, None
            has_quantifier = True
        elif char == "+":
            self._consume()
            min_cnt, max_cnt = 1, None
            has_quantifier = True
        elif char == "?":
            self._consume()
            min_cnt, max_cnt = 0, 1
            has_quantifier = True
        elif char == "{":
            save_pos = self.pos
            self._consume()
            content = ""
            while self.pos < self.length and self._peek() != "}":
                content += self._consume()
            if self._peek() == "}":
                self._consume()
                parts = content.split(",")
                try:
                    if len(parts) == 1:
                        val = int(parts[0])
                        min_cnt, max_cnt = val, val
                    elif len(parts) == 2:
                        min_cnt = int(parts[0]) if parts[0] else 0
                        max_cnt = int(parts[1]) if parts[1] else None
                    has_quantifier = True
                except ValueError:
                    self.pos = save_pos
            else:
                self.pos = save_pos

        if has_quantifier:
            greedy = True
            if self._peek() == "?":
                self._consume()
                greedy = False
            return QuantifierNode(node, min_cnt, max_cnt, greedy)

        return node
