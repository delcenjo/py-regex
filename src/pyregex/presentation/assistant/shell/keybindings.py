"""Nebula Shell — Custom Key Bindings."""

from __future__ import annotations
from prompt_toolkit.key_binding import KeyBindings


def create_keybindings() -> KeyBindings:
    """Create custom key bindings for the assistant REPL."""
    kb = KeyBindings()

    @kb.add("c-l")
    def clear_screen(event):
        """Clear screen."""
        event.app.renderer.clear()

    @kb.add("f1")
    def show_help(event):
        """F1 = Help."""
        buf = event.app.current_buffer
        buf.text = "help"
        buf.validate_and_handle()

    @kb.add("c-s")
    def show_status(event):
        """Ctrl+S = Status."""
        buf = event.app.current_buffer
        buf.text = "status"
        buf.validate_and_handle()

    return kb
