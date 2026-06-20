"""Nebula Assistant Engine — Session Context."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from pyregex.presentation.assistant.core.types import SessionState, WizardResult


@dataclass
class HistoryEntry:
    """A single entry in the session command history."""

    command: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    result: Optional[str] = None
    module: str = ""
    wizard: str = ""


class SessionContext:
    """
    Manages the full state of an interactive assistant session.

    Features:
    - Navigation stack (push/pop for back navigation)
    - Variable storage for cross-wizard data sharing
    - Undo/redo stack for pattern operations
    - Command history with timestamps
    - Generated pattern collection for the session
    """

    def __init__(self):
        # State
        self._state: SessionState = SessionState.IDLE
        self._state_stack: list[SessionState] = []

        # Navigation
        self._nav_stack: list[str] = []  # breadcrumb trail
        self._current_module: Optional[str] = None
        self._current_wizard: Optional[str] = None
        self._catalog_path: list[str] = [] # path in the catalog tree

        # Variables (shared between wizards in a session)
        self._variables: dict[str, Any] = {}

        # History
        self._command_history: list[HistoryEntry] = []
        self._generated_patterns: list[WizardResult] = []

        # Undo/Redo
        self._undo_stack: list[dict[str, Any]] = []
        self._redo_stack: list[dict[str, Any]] = []

        # Timestamps
        self.started_at: str = datetime.now().isoformat()
        self.last_activity: str = self.started_at

    @property
    def state(self) -> SessionState:
        return self._state

    def transition(self, new_state: SessionState) -> None:
        """Transition to a new state, pushing current state to stack."""
        self._state_stack.append(self._state)
        self._state = new_state
        self._touch()

    def restore_state(self) -> SessionState:
        """Pop and restore the previous state."""
        if self._state_stack:
            self._state = self._state_stack.pop()
        else:
            self._state = SessionState.IDLE
        self._touch()
        return self._state

    @property
    def breadcrumbs(self) -> list[str]:
        return list(self._nav_stack)

    @property
    def breadcrumb_str(self) -> str:
        return " > ".join(self._nav_stack) if self._nav_stack else "Home"

    def push_nav(self, location: str) -> None:
        """Push a location onto the navigation stack."""
        self._nav_stack.append(location)
        self._touch()

    def pop_nav(self) -> Optional[str]:
        """Pop and return the last navigation location."""
        if self._nav_stack:
            self._touch()
            return self._nav_stack.pop()
        return None

    def clear_nav(self) -> None:
        """Reset navigation to root."""
        self._nav_stack.clear()
        self._touch()

    @property
    def current_module(self) -> Optional[str]:
        return self._current_module

    @current_module.setter
    def current_module(self, value: Optional[str]) -> None:
        self._current_module = value
        self._touch()

    @property
    def current_wizard(self) -> Optional[str]:
        return self._current_wizard

    @current_wizard.setter
    def current_wizard(self, value: Optional[str]) -> None:
        self._current_wizard = value
        self._touch()

    @property
    def catalog_path(self) -> list[str]:
        return list(self._catalog_path)

    def push_catalog(self, part: str) -> None:
        self._catalog_path.append(part)
        self._touch()

    def pop_catalog(self) -> Optional[str]:
        if self._catalog_path:
            self._touch()
            return self._catalog_path.pop()
        return None

    def clear_catalog(self) -> None:
        self._catalog_path.clear()
        self._touch()

    def set(self, key: str, value: Any) -> None:
        """Store a session variable."""
        self._variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a session variable."""
        return self._variables.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._variables

    @property
    def variables(self) -> dict[str, Any]:
        return dict(self._variables)

    def record_command(self, command: str, result: Optional[str] = None) -> None:
        """Record a command in session history."""
        self._command_history.append(
            HistoryEntry(
                command=command,
                result=result,
                module=self._current_module or "",
                wizard=self._current_wizard or "",
            )
        )
        self._touch()

    @property
    def history(self) -> list[HistoryEntry]:
        return list(self._command_history)

    @property
    def history_count(self) -> int:
        return len(self._command_history)

    def add_pattern(self, result: WizardResult) -> None:
        """Add a generated pattern to the session collection."""
        self._generated_patterns.append(result)
        self._touch()

    @property
    def patterns(self) -> list[WizardResult]:
        return list(self._generated_patterns)

    @property
    def pattern_count(self) -> int:
        return len(self._generated_patterns)

    @property
    def last_pattern(self) -> Optional[WizardResult]:
        return self._generated_patterns[-1] if self._generated_patterns else None

    def push_undo(self, snapshot: dict[str, Any]) -> None:
        """Save a state snapshot for undo."""
        self._undo_stack.append(snapshot)
        self._redo_stack.clear()

    def undo(self) -> Optional[dict[str, Any]]:
        """Pop and return the last undo snapshot."""
        if self._undo_stack:
            snapshot = self._undo_stack.pop()
            self._redo_stack.append(snapshot)
            return snapshot
        return None

    def redo(self) -> Optional[dict[str, Any]]:
        """Pop and return the last redo snapshot."""
        if self._redo_stack:
            snapshot = self._redo_stack.pop()
            self._undo_stack.append(snapshot)
            return snapshot
        return None

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    def get_stats(self) -> dict[str, Any]:
        """Get session statistics."""
        return {
            "state": self._state.name,
            "commands_executed": len(self._command_history),
            "patterns_generated": len(self._generated_patterns),
            "variables_stored": len(self._variables),
            "nav_depth": len(self._nav_stack),
            "undo_available": len(self._undo_stack),
            "redo_available": len(self._redo_stack),
            "started_at": self.started_at,
            "last_activity": self.last_activity,
        }

    def _touch(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now().isoformat()

    def reset(self) -> None:
        """Reset the entire session to initial state."""
        self.__init__()
