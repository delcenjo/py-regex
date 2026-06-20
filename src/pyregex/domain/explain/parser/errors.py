from __future__ import annotations


class ParserError(Exception):
    """Raised when the AST Parser encounters structurally invalid token combinations."""

    def __init__(self, message: str, start: int, end: int):
        self.message = message
        self.start = start
        self.end = end
        super().__init__(f"Syntax Error [{start}:{end}]: {message}")
