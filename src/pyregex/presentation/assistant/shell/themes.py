"""Nebula Shell — Color Themes."""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Theme:
    """Color scheme for the assistant shell."""

    name: str
    # Prompt colors
    prompt_prefix: str = "#61afef"  # Blue
    prompt_path: str = "#98c379"  # Green
    prompt_arrow: str = "#c678dd"  # Purple
    # UI colors
    header_bg: str = "#282c34"
    header_fg: str = "#abb2bf"
    accent: str = "#61afef"
    success: str = "#98c379"
    warning: str = "#e5c07b"
    error: str = "#e06c75"
    dim: str = "#5c6370"
    # Toolbar
    toolbar_bg: str = "#21252b"
    toolbar_fg: str = "#abb2bf"
    toolbar_key: str = "#c678dd"


THEMES = {
    "dark": Theme(
        name="dark",
        prompt_prefix="#61afef",
        prompt_path="#98c379",
        prompt_arrow="#c678dd",
        accent="#61afef",
        success="#98c379",
        warning="#e5c07b",
        error="#e06c75",
    ),
    "light": Theme(
        name="light",
        prompt_prefix="#4078f2",
        prompt_path="#50a14f",
        prompt_arrow="#a626a4",
        header_bg="#fafafa",
        header_fg="#383a42",
        accent="#4078f2",
        success="#50a14f",
        warning="#c18401",
        error="#e45649",
        dim="#a0a1a7",
        toolbar_bg="#e5e5e6",
        toolbar_fg="#383a42",
    ),
    "monokai": Theme(
        name="monokai",
        prompt_prefix="#66d9ef",
        prompt_path="#a6e22e",
        prompt_arrow="#ae81ff",
        header_bg="#272822",
        header_fg="#f8f8f2",
        accent="#66d9ef",
        success="#a6e22e",
        warning="#e6db74",
        error="#f92672",
        dim="#75715e",
        toolbar_bg="#1e1f1c",
    ),
    "nord": Theme(
        name="nord",
        prompt_prefix="#88c0d0",
        prompt_path="#a3be8c",
        prompt_arrow="#b48ead",
        header_bg="#2e3440",
        header_fg="#d8dee9",
        accent="#88c0d0",
        success="#a3be8c",
        warning="#ebcb8b",
        error="#bf616a",
        dim="#4c566a",
        toolbar_bg="#3b4252",
    ),
}


def get_theme(name: str = "dark") -> Theme:
    """Get a theme by name, defaulting to dark."""
    return THEMES.get(name, THEMES["dark"])
