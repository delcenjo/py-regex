"""Nebula — UI Components (tables, panels, menus, progress)."""

from __future__ import annotations
from pyregex.utils import ansi


class Table:
    """Render a formatted table."""

    def __init__(self, headers: list[str], rows: list[list[str]], title: str = ""):
        self.headers = headers
        self.rows = rows
        self.title = title

    def render(self) -> str:
        widths = [
            max(len(h), max((len(str(r[i])) for r in self.rows), default=0))
            for i, h in enumerate(self.headers)
        ]
        lines = []
        if self.title:
            lines.append(f"\n  {ansi.bold(self.title)}")
        sep = "─" * (sum(widths) + 3 * len(widths) + 1)
        lines.append(f"  ┌{sep}┐")
        header = (
            "  │ " + " │ ".join(h.ljust(w) for h, w in zip(self.headers, widths)) + " │"
        )
        lines.append(ansi.bold(header))
        lines.append(f"  ├{sep}┤")
        for row in self.rows:
            line = (
                "  │ " + " │ ".join(str(c).ljust(w) for c, w in zip(row, widths)) + " │"
            )
            lines.append(line)
        lines.append(f"  └{sep}┘")
        return "\n".join(lines)

    def print(self):
        print(self.render())


class Panel:
    """Render a bordered panel."""

    def __init__(self, content: str, title: str = "", width: int = 55):
        self.content = content
        self.title = title
        self.width = width

    def print(self):
        print(f"\n  {'━' * self.width}")
        if self.title:
            print(f"  {ansi.bold(self.title)}")
        for line in self.content.split("\n"):
            print(f"  {line}")
        print(f"  {'━' * self.width}")


class ProgressBar:
    """Render a progress bar."""

    def __init__(self, current: int, total: int, width: int = 30, label: str = ""):
        self.current = current
        self.total = total
        self.width = width
        self.label = label

    def render(self) -> str:
        filled = int((self.current / max(self.total, 1)) * self.width)
        bar = "█" * filled + "░" * (self.width - filled)
        pct = int((self.current / max(self.total, 1)) * 100)
        return f"  [{bar}] {pct}% {self.label}"

    def print(self):
        print(self.render())


class Menu:
    """Render an interactive menu."""

    def __init__(self, items: list[tuple[str, str, str]], title: str = ""):
        self.items = items  # (key, label, description)
        self.title = title

    def print(self):
        if self.title:
            print(f"\n  {ansi.bold(self.title)}")
        for key, label, desc in self.items:
            print(f"    [{key}] {label}")
            if desc:
                print(f"        {ansi.dim(desc)}")
