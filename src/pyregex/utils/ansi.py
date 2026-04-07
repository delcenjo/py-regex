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


def print_banner(title: str) -> None:
    """Print a styled banner."""
    print()
    print_separator()
    print(header(f"  {title}"))
    print_separator()
    print()
