from __future__ import annotations
import sys
from pyregex.utils import ansi
from pyregex.utils.ansi import strip_ansi


class Table:
    """Render a high-density professional data table."""

    def __init__(self, headers: list[str], rows: list[list[str]], title: str = "", theme: str = "expert"):
        self.headers = headers
        self.rows = rows
        self.title = title
        from pyregex.presentation.assistant.shell.themes import get_theme
        self.theme = get_theme(theme)

    def render(self) -> str:
        widths = [
            max(ansi.visible_len(h), max((ansi.visible_len(str(r[i])) for r in self.rows), default=0))
            for i, h in enumerate(self.headers)
        ]
        lines = []
        
        TL, TR, BL, BR = "┌", "┐", "└", "┘"
        H, V = "─", "│"
        LT, RT, TT, BT, CT = "├", "┤", "┬", "┴", "┼"

        if self.title:
            lines.append(f"\n  {ansi.fg_hex(self.theme.accent, f'◆ {self.title.upper()}')}")

        top_h = "  " + TL + TT.join(H * (w + 2) for w in widths) + TR
        mid_h = "  " + LT + CT.join(H * (w + 2) for w in widths) + RT
        bot_h = "  " + BL + BT.join(H * (w + 2) for w in widths) + BR

        header_cells = []
        for h, w in zip(self.headers, widths):
            text = ansi.bold(h)
            v_len = ansi.visible_len(text)
            pad = w - v_len
            left_pad = pad // 2
            right_pad = pad - left_pad
            header_cells.append(f" {' ' * left_pad}{text}{' ' * right_pad} ")

        header_row = "  " + V + V.join(header_cells) + V
        
        lines.append(ansi.fg_hex(self.theme.dim, top_h))
        lines.append(header_row)
        lines.append(ansi.fg_hex(self.theme.dim, mid_h))

        for row in self.rows:
            formatted_cells = []
            for i, cell in enumerate(row):
                val = str(cell)
                v_len = ansi.visible_len(val)
                pad = widths[i] - v_len
                
                if strip_ansi(val).isdigit():
                    formatted_cells.append(f" {' ' * pad}{val} ")
                else:
                    formatted_cells.append(f" {val}{' ' * pad} ")
            
            line = "  " + V + V.join(formatted_cells) + V
            lines.append(line)

        lines.append(ansi.fg_hex(self.theme.dim, bot_h))
        return "\n".join(lines)

    def print(self):
        print(self.render())


class Panel:
    """Render a technical bordered panel with expert styling."""

    def __init__(self, content: str, title: str = "", theme: str = "expert", width: int = 65):
        self.content = content
        self.title = title
        self.width = width
        from pyregex.presentation.assistant.shell.themes import get_theme
        self.theme = get_theme(theme)

    def print(self):
        border_color = self.theme.dim
        accent_color = self.theme.accent
        
        print(f"\n  {ansi.fg_hex(border_color, '╭' + '─' * (self.width - 2) + '╮')}")
        if self.title:
            title_text = self.title.upper()
            v_len = ansi.visible_len(title_text)
            pad = self.width - 4 - v_len
            print(f"  {ansi.fg_hex(border_color, '│')} {ansi.color(title_text, fg=accent_color, bold=True)}{' ' * pad} {ansi.fg_hex(border_color, '│')}")
            print(f"  {ansi.fg_hex(border_color, '├' + '─' * (self.width - 2) + '┤')}")
            
        for line in self.content.split("\n"):
            clean_line = line.strip()
            v_len = ansi.visible_len(clean_line)
            if v_len > self.width - 4:
                clean_line = clean_line[: self.width - 7] + "..."
                v_len = self.width - 4
            
            pad = self.width - 4 - v_len
            print(f"  {ansi.fg_hex(border_color, '│')} {clean_line}{' ' * pad} {ansi.fg_hex(border_color, '│')}")
            
        print(f"  {ansi.fg_hex(border_color, '╰' + '─' * (self.width - 2) + '╯')}")


class ProgressBar:
    """Render a professional expert-style progress bar."""

    def __init__(self, current: int, total: int, width: int = 40, label: str = "", theme: str = "expert"):
        self.current = current
        self.total = total
        self.width = width
        self.label = label
        from pyregex.presentation.assistant.shell.themes import get_theme
        self.theme = get_theme(theme)

    def render(self) -> str:
        ratio = self.current / max(self.total, 1)
        filled = int(ratio * self.width)
        bar = "█" * filled + ansi.fg_hex(self.theme.dim, " " * (self.width - filled))
        pct = int(ratio * 100)
        return f"  {ansi.fg_hex(self.theme.accent, '▕')}{bar}{ansi.fg_hex(self.theme.accent, '▏')} {ansi.bold(f'{pct}%')} {ansi.dim(self.label)}"

    def print(self):
        print(self.render())


class Menu:
    """Render a sophisticated interactive menu."""

    def __init__(self, items: list[tuple[str, str, str]], title: str = "", theme: str = "expert"):
        self.items = items
        self.title = title
        from pyregex.presentation.assistant.shell.themes import get_theme
        self.theme = get_theme(theme)

    def print(self):
        if self.title:
            print(f"\n  {ansi.color(self.title.upper(), fg=self.theme.accent, bold=True)}")
        
        if not self.items:
            print(f"    {ansi.dim('(No data available in this context)')}")
            return

        for key, label, desc in self.items:
            key_styled = ansi.color(f" {key} ", fg=self.theme.header_fg, bg=self.theme.toolbar_bg, bold=True)
            print(f"    {key_styled} {ansi.bold(label)}")
            if desc:
                print(f"        {ansi.fg_hex(self.theme.dim, '└─ ' + desc)}")


class StatusSpinner:
    """A professional non-blocking spinner for long operations."""
    
    def __init__(self, label: str = "Processing", theme: str = "expert"):
        self.label = label
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current = 0
        from pyregex.presentation.assistant.shell.themes import get_theme
        self.theme = get_theme(theme)

    def next(self):
        frame = self.frames[self.current % len(self.frames)]
        sys.stdout.write(f"\r  {ansi.fg_hex(self.theme.accent, frame)} {ansi.bold(self.label)}...")
        sys.stdout.flush()
        self.current += 1
