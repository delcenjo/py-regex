"""Nebula Assistant Engine — Configuration."""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class AssistantConfig:
    """Configuration for the assistant engine."""

    # UI
    theme: str = "expert"
    show_banner: bool = True
    show_toolbar: bool = True
    show_breadcrumbs: bool = True
    show_tips: bool = True

    # Behavior
    auto_preview: bool = True  # Show live regex preview after each step
    auto_save_session: bool = False  # Auto-save session to disk
    max_history: int = 500  # Max entries in command history
    max_undo: int = 50  # Max undo levels

    # Wizard
    wizard_confirm_cancel: bool = True  # Ask before cancelling wizard
    wizard_show_progress: bool = True  # Show progress indicator
    wizard_default_timeout: int = 0  # Step timeout in seconds (0 = no timeout)

    # Modules
    disabled_modules: list[str] = field(default_factory=list)
    module_search_paths: list[str] = field(default_factory=list)

    # Shell
    prompt_style: str = "full"  # "full", "short", "minimal"
    enable_syntax_highlight: bool = True
    enable_auto_suggest: bool = True
    enable_mouse: bool = False

    # Language
    language: str = "es"  # Default language
