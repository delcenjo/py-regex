"""Nebula Shell — Status Toolbar."""

from __future__ import annotations
from typing import Optional

from prompt_toolkit.formatted_text import HTML

from pyregex.presentation.assistant.core.session import SessionContext
from pyregex.presentation.assistant.core.state.machine import StateMachine
from pyregex.presentation.assistant.shell.themes import Theme, get_theme


class StatusToolbar:
    """
    Bottom toolbar for the assistant REPL.

    Shows: [State] | Breadcrumbs | Patterns: N | [Shortcuts]
    """

    def __init__(
        self, session: SessionContext, fsm: StateMachine, theme: Optional[Theme] = None
    ):
        self.session = session
        self.fsm = fsm
        self.theme = theme or get_theme()

    def get_toolbar(self) -> HTML:
        """Return formatted toolbar text for prompt_toolkit with expert styling."""
        state = self.fsm.state.name
        breadcrumbs = self.session.breadcrumb_str
        patterns = self.session.pattern_count
        commands = self.session.history_count
        
        # Expert palette (Hex)
        accent = self.theme.accent
        dim = self.theme.dim
        
        parts = [
            f"<ansiblue><b>[ {state} ]</b></ansiblue>",
            f"<ansigreen>LOC:</ansigreen> <ansiwhite>{breadcrumbs or '~'}</ansiwhite>",
            f"<ansiyellow>PKG:</ansiyellow> <ansiwhite>{patterns}</ansiwhite>",
            f"<ansimagenta>CMD:</ansimagenta> <ansiwhite>{commands}</ansiwhite>",
        ]

        # Shortcuts hint based on state (Expert style: minimalist labels)
        if state == "IDLE":
            hint = "help | personal | web | security | devops"
        elif state == "BROWSING":
            hint = "email | phone | url | id | back"
        elif state == "IN_MODULE":
            hint = "[id] | back | catalog"
        elif state == "IN_WIZARD":
            hint = "b:prev | ^C:abort"
        else:
            hint = "help | back | quit"
            
        parts.append(f"<ansicyan><b></b> {hint}</ansicyan>")

        return HTML(f" <b>{'  ' + '   '.join(parts)}</b> ")

    def __call__(self) -> HTML:
        """Make toolbar callable for prompt_toolkit."""
        return self.get_toolbar()
