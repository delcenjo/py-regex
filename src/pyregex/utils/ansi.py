"""ANSI escape code utilities for terminal output styling."""

from __future__ import annotations

import os
import sys


def _supports_color() -> bool:
    """Check if the terminal supports ANSI color codes."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


SUPPORTS_COLOR: bool = _supports_color()

# Reset
RESET = "\033[0m"

# Styles
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Foreground colors
FG_BLACK = "\033[30m"
FG_RED = "\033[31m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"
FG_BLUE = "\033[34m"
FG_MAGENTA = "\033[35m"
FG_CYAN = "\033[36m"
FG_WHITE = "\033[37m"
FG_BRIGHT_BLACK = "\033[90m"
FG_BRIGHT_RED = "\033[91m"
FG_BRIGHT_GREEN = "\033[92m"
FG_BRIGHT_YELLOW = "\033[93m"
FG_BRIGHT_BLUE = "\033[94m"
FG_BRIGHT_MAGENTA = "\033[95m"
FG_BRIGHT_CYAN = "\033[96m"

# Background colors
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"


def _wrap(code: str, text: str) -> str:
    """Wrap text with ANSI code if color is supported."""
    if not SUPPORTS_COLOR:
        return text
    return f"{code}{text}{RESET}"


def bold(text: str) -> str:
    return _wrap(BOLD, text)


def dim(text: str) -> str:
    return _wrap(DIM, text)


def italic(text: str) -> str:
    return _wrap(ITALIC, text)


def underline(text: str) -> str:
    return _wrap(UNDERLINE, text)


def success(text: str) -> str:
    return _wrap(FG_GREEN, text)


def error(text: str) -> str:
    return _wrap(FG_RED, text)


def warning(text: str) -> str:
    return _wrap(FG_YELLOW, text)


def info(text: str) -> str:
    return _wrap(FG_CYAN, text)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string (e.g., '#ffffff' or 'ffffff') to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def fg_hex(hex_str: str, text: str) -> str:
    """Wrap text with a TrueColor foreground hex color."""
    if not SUPPORTS_COLOR:
        return text
    r, g, b = hex_to_rgb(hex_str)
    return f"\033[38;2;{r};{g};{b}m{text}{RESET}"


def bg_hex(hex_str: str, text: str) -> str:
    """Wrap text with a TrueColor background hex color."""
    if not SUPPORTS_COLOR:
        return text
    r, g, b = hex_to_rgb(hex_str)
    return f"\033[48;2;{r};{g};{b}m{text}{RESET}"


def color(text: str, fg: str | None = None, bg: str | None = None, bold: bool = False) -> str:
    """Apply complex styling including TrueColor to text."""
    if not SUPPORTS_COLOR:
        return text
    
    parts = []
    if bold:
        parts.append("\033[1m")
    if fg:
        r, g, b = hex_to_rgb(fg)
        parts.append(f"\033[38;2;{r};{g};{b}m")
    if bg:
        r, g, b = hex_to_rgb(bg)
        parts.append(f"\033[48;2;{r};{g};{b}m")
        
    if not parts:
        return text
        
    return f"{''.join(parts)}{text}{RESET}"


def get_highlight_color(index: int) -> str:
    """Return a background color based on index for multi-pattern highlighting."""
    colors = [BG_YELLOW, BG_CYAN, BG_MAGENTA, BG_GREEN, BG_BLUE]
    return colors[index % len(colors)]


def highlight(text: str, color_index: int = 0) -> str:
    """Highlight text with a background color for match display."""
    if not SUPPORTS_COLOR:
        return f"[{text}]"
    color = get_highlight_color(color_index)
    return f"{color}{FG_BLACK}{BOLD}{text}{RESET}"


def header(text: str) -> str:
    return _wrap(BOLD + FG_BRIGHT_CYAN, text)


def muted(text: str) -> str:
    return _wrap(FG_BRIGHT_BLACK, text)


def label(text: str) -> str:
    return _wrap(BOLD + FG_BRIGHT_MAGENTA, text)


def regex_display(text: str) -> str:
    return _wrap(BOLD + FG_BRIGHT_GREEN, text)


def print_separator(char: str = "─", width: int = 50) -> None:
    """Print a separator line."""
    print(muted(char * width))


def banner(text: str) -> str:
    """Return a stylized banner string."""
    width = 60
    line = muted("═" * width)
    header_text = header(text.upper())
    padding = max(0, (width - visible_len(text)) // 2)
    centered_header = " " * padding + header_text
    return f"\n{line}\n{centered_header}\n{line}\n"


def print_banner(text: str) -> None:
    """Print a stylized banner."""
    print(banner(text))


import re
import unicodedata

ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape codes from the text."""
    if not isinstance(text, str):
        return str(text)
    return ANSI_ESCAPE.sub("", text)


def display_width(text: str) -> int:
    """Calculate the visual column width of a string, accounting for wide characters (emojis) 
    and skipping zero-width characters (variation selectors, marks)."""
    clean_text = strip_ansi(text)
    width = 0
    for char in clean_text:
        # Mn/Me/Cf are zero-width (combining marks, format chars)
        cat = unicodedata.category(char)
        if cat in ("Mn", "Me", "Cf"):
            continue
        if unicodedata.east_asian_width(char) in ("W", "F"):
            width += 2
        else:
            width += 1
    return width


def visible_len(text: str) -> int:
    """Calculate the visible width of a string, ignoring ANSI codes and accounting for wide chars."""
    return display_width(text)
