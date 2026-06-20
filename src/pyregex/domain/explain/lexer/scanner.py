# src/pyregex/domain/explain/lexer/scanner.py
from __future__ import annotations
from typing import List
from pyregex.domain.explain.models.tokens import Token, TokenType


class RegexScannerError(Exception):
    """Raised for lexical errors during regex tokenization."""

    pass


class Scanner:
    """Lexical analyzer for Regular Expressions.

    Converts a raw string into a stream of strictly typed Tokens.
    """

    def __init__(self, pattern: str):
        self.pattern = pattern
        self.length = len(pattern)
        self.pos = 0
        self.in_char_class = False

    def scan(self) -> List[Token]:
        """Runs the lexer and returns all tokens."""
        tokens = []
        while self.pos < self.length:
            tokens.append(self._next_token())
        tokens.append(Token(TokenType.EOF, "", self.length, self.length))
        return tokens

    def _peek(self, offset: int = 1) -> str:
        """Returns the character ahead without consuming it."""
        idx = self.pos + offset - 1
        if idx >= self.length:
            return ""
        return self.pattern[idx]

    def _next_token(self) -> Token:
        char = self.pattern[self.pos]
        start = self.pos

        # Inside character class rules `[...]`
        if self.in_char_class:
            if char == "]":
                self.in_char_class = False
                self.pos += 1
                return Token(TokenType.CLASS_END, char, start, self.pos)
            if char == "-":
                self.pos += 1
                return Token(TokenType.CLASS_RANGE, char, start, self.pos)
            if char == "\\":
                return self._handle_escape()
            self.pos += 1
            return Token(TokenType.LITERAL, char, start, self.pos)

        # Standard context rules
        if char == "\\":
            return self._handle_escape()

        if char == "^":
            self.pos += 1
            return Token(TokenType.START_ANCHOR, char, start, self.pos)
        if char == "$":
            self.pos += 1
            return Token(TokenType.END_ANCHOR, char, start, self.pos)

        if char in ("*", "+", "?"):
            # Check for LAZY modifier
            self.pos += 1
            if self._peek() == "?":
                self.pos += 1
                return Token(TokenType.QUANTIFIER, char + "?", start, self.pos)
            return Token(TokenType.QUANTIFIER, char, start, self.pos)

        if char == "{":
            return self._handle_braces(start)

        if char == ".":
            self.pos += 1
            return Token(TokenType.DOT, char, start, self.pos)

        if char == "|":
            self.pos += 1
            return Token(TokenType.ALTERNATION, char, start, self.pos)

        if char == "(":
            return self._handle_group_start(start)

        if char == ")":
            self.pos += 1
            return Token(TokenType.GROUP_END, char, start, self.pos)

        if char == "[":
            self.in_char_class = True
            self.pos += 1
            val = "["
            if self._peek() == "^":
                self.pos += 1
                val = "[^"
            return Token(TokenType.CLASS_START, val, start, self.pos)

        # Everything else is a literal
        self.pos += 1
        return Token(TokenType.LITERAL, char, start, self.pos)

    def _handle_escape(self) -> Token:
        start = self.pos
        self.pos += 1
        if self.pos >= self.length:
            raise RegexScannerError(f"Dangling escape at end of pattern (col {start})")

        esc_char = self.pattern[self.pos]
        self.pos += 1

        val = "\\" + esc_char

        if esc_char in ("A", "Z", "z"):
            return Token(
                TokenType.START_ANCHOR if esc_char == "A" else TokenType.END_ANCHOR,
                val,
                start,
                self.pos,
            )
        if esc_char in ("b", "B"):
            return Token(TokenType.WORD_BOUNDARY, val, start, self.pos)
        if esc_char in ("d", "D", "w", "W", "s", "S"):
            return Token(TokenType.CHAR_CLASS, val, start, self.pos)
        if esc_char.isdigit():
            return Token(TokenType.BACKREFERENCE, val, start, self.pos)

        return Token(TokenType.LITERAL, val, start, self.pos)

    def _handle_braces(self, start: int) -> Token:
        # Tries to parse {n} or {n,m}. If not matched, returns literal '{'
        temp_pos = self.pos + 1
        content = ""
        while temp_pos < self.length and self.pattern[temp_pos] != "}":
            content += self.pattern[temp_pos]
            temp_pos += 1

        if temp_pos < self.length and self.pattern[temp_pos] == "}":
            clean = content.replace(",", "").strip()
            if clean.isdigit() or content == ",":
                self.pos = temp_pos + 1
                val = "{" + content + "}"
                if self._peek() == "?":
                    self.pos += 1
                    val += "?"
                return Token(TokenType.QUANTIFIER, val, start, self.pos)

        self.pos += 1
        return Token(TokenType.LITERAL, "{", start, self.pos)

    def _handle_group_start(self, start: int) -> Token:
        self.pos += 1
        val = "("

        if self._peek() == "?":
            self.pos += 1
            val = "(?"
            next_c = self._peek()

            if next_c == ":":
                self.pos += 1
                val += ":"
            elif next_c in ("=", "!"):
                self.pos += 1
                val += next_c
            elif next_c == "<":
                self.pos += 1
                val += "<"
                if self._peek() in ("=", "!"):
                    val += self._peek()
                    self.pos += 1
                else:
                    # Named group (?<name> or (?P<name>
                    pass
            elif next_c == "P":
                if self._peek(2) == "<":
                    self.pos += 2
                    val += "P<"
                    while self.pos < self.length and self.pattern[self.pos] != ">":
                        val += self.pattern[self.pos]
                        self.pos += 1
                    if self.pos < self.length:
                        val += ">"
                        self.pos += 1
            elif next_c in ("i", "m", "s", "x", "-"):
                # Flags toggle
                while self.pos < self.length and self.pattern[self.pos] in (
                    "i",
                    "m",
                    "s",
                    "x",
                    "-",
                    "a",
                    "L",
                    "u",
                ):
                    val += self.pattern[self.pos]
                    self.pos += 1
                if self.pos < self.length and self.pattern[self.pos] == ")":
                    val += ")"
                    self.pos += 1
                    return Token(TokenType.FLAG_SET, val, start, self.pos)
                elif self.pos < self.length and self.pattern[self.pos] == ":":
                    val += ":"
                    self.pos += 1

        return Token(TokenType.GROUP_START, val, start, self.pos)
