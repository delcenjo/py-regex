from __future__ import annotations
from typing import List, Optional

from pyregex.domain.explain.models.tokens import Token, TokenType
from pyregex.domain.explain.models.ast import (
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
    AstNode,
)
from pyregex.domain.explain.parser.errors import ParserError


class RecursiveDescentParser:
    """Builds an Abstract Syntax Tree (AST) from a stream of Regex Tokens."""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.length = len(tokens)

    def parse(self) -> RootNode:
        root = RootNode()
        root.children = self._parse_alternation()
        if self._peek().type != TokenType.EOF:
            t = self._peek()
            raise ParserError(
                f"Unexpected token {t.type.name} '{t.value}'", t.start, t.end
            )
        return root

    def _peek(self, offset: int = 0) -> Token:
        idx = self.pos + offset
        if idx >= self.length:
            return self.tokens[-1]
        return self.tokens[idx]

    def _consume(self, expected_type: Optional[TokenType] = None) -> Token:
        t = self._peek()
        if expected_type and t.type != expected_type:
            raise ParserError(
                f"Expected {expected_type.name}, got {t.type.name}", t.start, t.end
            )
        self.pos += 1
        return t

    def _parse_alternation(self) -> List[AstNode]:
        left_nodes = self._parse_sequence()

        if self._peek().type == TokenType.ALTERNATION:
            self._consume(TokenType.ALTERNATION)
            right_nodes = self._parse_alternation()

            left = (
                RootNode(children=left_nodes)
                if len(left_nodes) > 1
                else (left_nodes[0] if left_nodes else RootNode())
            )
            right = (
                RootNode(children=right_nodes)
                if len(right_nodes) > 1
                else (right_nodes[0] if right_nodes else RootNode())
            )

            return [AlternationNode(left=left, right=right)]

        return left_nodes

    def _parse_sequence(self) -> List[AstNode]:
        nodes = []
        while self.pos < self.length:
            t = self._peek()
            if t.type in (TokenType.EOF, TokenType.ALTERNATION, TokenType.GROUP_END):
                break

            if t.type == TokenType.QUANTIFIER:
                quant = self._consume()
                if not nodes:
                    raise ParserError(
                        f"Quantifier '{quant.value}' without preceding token",
                        quant.start,
                        quant.end,
                    )
                prev = nodes.pop()
                if isinstance(prev, QuantifierNode):
                    raise ParserError(
                        "Multiple quantifiers applied consecutively",
                        quant.start,
                        quant.end,
                    )
                nodes.append(self._build_quantifier(quant, prev))
            else:
                nodes.append(self._parse_node())

        return nodes

    def _parse_node(self) -> AstNode:
        t = self._consume()

        if t.type == TokenType.LITERAL:
            return LiteralNode(t.value)
        elif t.type == TokenType.DOT:
            return DotNode()
        elif t.type == TokenType.START_ANCHOR:
            return AnchorNode("start", t.value)
        elif t.type == TokenType.END_ANCHOR:
            return AnchorNode("end", t.value)
        elif t.type == TokenType.WORD_BOUNDARY:
            return AnchorNode(
                "word_boundary" if "b" in t.value else "non_word_boundary", t.value
            )
        elif t.type == TokenType.CHAR_CLASS:
            val = t.value[1]
            negated = val.isupper()
            type_map = {
                "d": "digit",
                "D": "digit",
                "w": "word",
                "W": "word",
                "s": "whitespace",
                "S": "whitespace",
            }
            return CharClassNode(
                type=type_map.get(val, "unknown"), negated=negated, value=t.value
            )
        elif t.type == TokenType.BACKREFERENCE:
            return BackreferenceNode(t.value[1:])
        elif t.type == TokenType.FLAG_SET:
            return FlagNode(flags_added=t.value, flags_removed="")
        elif t.type == TokenType.GROUP_START:
            return self._parse_group(t)
        elif t.type == TokenType.CLASS_START:
            return self._parse_character_class(t)

        raise ParserError(
            f"Unhandled token while parsing: {t.type.name} '{t.value}'", t.start, t.end
        )

    def _parse_group(self, start_token: Token) -> GroupNode:
        val = start_token.value
        g_type = "capture"
        name = None

        if val == "(?:":
            g_type = "non_capture"
        elif val == "(?=":
            g_type = "lookahead"
        elif val == "(?!":
            g_type = "negative_lookahead"
        elif val == "(?<=":
            g_type = "lookbehind"
        elif val == "(?<!":
            g_type = "negative_lookbehind"
        elif val.startswith("(?P<"):
            g_type = "capture"
            name = val[4:-1]

        children = self._parse_alternation()
        self._consume(TokenType.GROUP_END)
        return GroupNode(type=g_type, name=name, children=children)

    def _parse_character_class(self, start_token: Token) -> SetClassNode:
        negated = start_token.value == "[^"
        items = []

        while self._peek().type not in (TokenType.CLASS_END, TokenType.EOF):
            t = self._consume()
            if t.type == TokenType.LITERAL:
                if self._peek().type == TokenType.CLASS_RANGE:
                    self._consume()
                    end_t = self._consume(TokenType.LITERAL)
                    items.append(RangeNode(t.value, end_t.value))
                else:
                    items.append(LiteralNode(t.value))
            elif t.type == TokenType.CHAR_CLASS:
                val = t.value[1]
                type_map = {
                    "d": "digit",
                    "D": "digit",
                    "w": "word",
                    "W": "word",
                    "s": "whitespace",
                    "S": "whitespace",
                }
                items.append(
                    CharClassNode(
                        type=type_map.get(val, "unknown"),
                        negated=val.isupper(),
                        value=t.value,
                    )
                )
            elif t.type == TokenType.CLASS_RANGE:
                # Literal hyphen at start/end of class
                items.append(LiteralNode("-"))
            else:
                items.append(LiteralNode(t.value))  # Fallback inside classes

        self._consume(TokenType.CLASS_END)
        return SetClassNode(negated=negated, items=items)

    def _build_quantifier(self, token: Token, child: AstNode) -> QuantifierNode:
        val = token.value
        greedy = True

        if val.endswith("?"):
            greedy = False
            val = val[:-1]

        min_v, max_v = 1, 1

        if val == "*":
            min_v, max_v = 0, None
        elif val == "+":
            min_v, max_v = 1, None
        elif val == "?":
            min_v, max_v = 0, 1
        elif val.startswith("{"):
            inner = val[1:-1]
            if "," in inner:
                parts = inner.split(",")
                min_v = int(parts[0]) if parts[0] else 0
                max_v = int(parts[1]) if parts[1] else None
            else:
                min_v = int(inner)
                max_v = min_v

        return QuantifierNode(min=min_v, max=max_v, greedy=greedy, child=child)
