"""Playground — Flag Manager.

Manages regex flags with display, toggle, and inline flag conversion.
"""

from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass
class FlagInfo:
    """Info about a single regex flag."""

    flag: int
    char: str
    name: str
    description: str
    active: bool = False

    @property
    def display(self) -> str:
        marker = "●" if self.active else "○"
        return f"[{self.char}] {marker} {self.name}"


class FlagManager:
    """Manages regex flag state and provides display/conversion utilities."""

    FLAGS = [
        FlagInfo(
            re.IGNORECASE,
            "i",
            "Case-insensitive",
            "Mayúsculas y minúsculas se tratan igual",
        ),
        FlagInfo(
            re.MULTILINE,
            "m",
            "Multi-line",
            "^ y $ coinciden inicio/fin de línea (no solo string)",
        ),
        FlagInfo(
            re.DOTALL, "s", "Dot-all", "El . también coincide con saltos de línea"
        ),
        FlagInfo(
            re.VERBOSE, "x", "Verbose", "Permite comentarios y espacios en el patrón"
        ),
        FlagInfo(re.ASCII, "a", "ASCII", "\\w \\b \\d solo ASCII (no unicode)"),
        FlagInfo(
            re.UNICODE, "u", "Unicode", "\\w \\b \\d con soporte Unicode completo"
        ),
    ]

    def __init__(self, initial_flags: int = 0):
        self._flags = initial_flags

    @property
    def flags(self) -> int:
        return self._flags

    @flags.setter
    def flags(self, value: int):
        self._flags = value

    def toggle(self, flag: int) -> int:
        """Toggle a flag and return new flags value."""
        self._flags ^= flag
        return self._flags

    def set(self, flag: int) -> None:
        self._flags |= flag

    def unset(self, flag: int) -> None:
        self._flags &= ~flag

    def is_active(self, flag: int) -> bool:
        return bool(self._flags & flag)

    def get_all(self) -> list[FlagInfo]:
        """Get all flags with current active state."""
        result = []
        for f in self.FLAGS:
            result.append(
                FlagInfo(
                    flag=f.flag,
                    char=f.char,
                    name=f.name,
                    description=f.description,
                    active=self.is_active(f.flag),
                )
            )
        return result

    def get_active(self) -> list[FlagInfo]:
        """Get only active flags."""
        return [f for f in self.get_all() if f.active]

    def to_inline_string(self) -> str:
        """Convert to inline flag string like (?ims)."""
        chars = [f.char for f in self.get_active()]
        return f"(?{''.join(chars)})" if chars else ""

    def to_python_flags(self) -> str:
        """Convert to Python re flags string."""
        parts = []
        mapping = {
            re.IGNORECASE: "re.IGNORECASE",
            re.MULTILINE: "re.MULTILINE",
            re.DOTALL: "re.DOTALL",
            re.VERBOSE: "re.VERBOSE",
            re.ASCII: "re.ASCII",
            re.UNICODE: "re.UNICODE",
        }
        for flag, name in mapping.items():
            if self.is_active(flag):
                parts.append(name)
        return " | ".join(parts) if parts else "0"

    def format_toolbar(self) -> str:
        """Format flags as toolbar display."""
        parts = []
        for f in self.get_all():
            if f.active:
                parts.append(f"[{f.char}]")
            else:
                parts.append(f" {f.char} ")
        return " ".join(parts)

    def by_char(self, char: str) -> FlagInfo | None:
        """Get flag info by character."""
        for f in self.FLAGS:
            if f.char == char:
                return f
        return None

    def toggle_by_char(self, char: str) -> int:
        """Toggle a flag by its character identifier."""
        info = self.by_char(char)
        if info:
            return self.toggle(info.flag)
        return self._flags
