"""Playground — Undo/Redo History Manager."""

from __future__ import annotations
from typing import Any


class UndoManager:
    """Manages undo/redo history with state snapshots."""

    def __init__(self, max_history: int = 100):
        self._history: list[dict[str, Any]] = []
        self._position: int = -1
        self._max_history = max_history
        self._is_restoring = False

    def push(self, snapshot: dict[str, Any]) -> None:
        """Push a new state snapshot. Clears any redo history."""
        if self._is_restoring:
            return

        # If we're not at the end, truncate redo history
        if self._position < len(self._history) - 1:
            self._history = self._history[: self._position + 1]

        self._history.append(snapshot)
        self._position = len(self._history) - 1

        # Limit history size
        if len(self._history) > self._max_history:
            excess = len(self._history) - self._max_history
            self._history = self._history[excess:]
            self._position -= excess

    def undo(self) -> dict[str, Any] | None:
        """Go back one step. Returns the previous snapshot or None."""
        if self._position <= 0:
            return None
        self._position -= 1
        return self._history[self._position].copy()

    def redo(self) -> dict[str, Any] | None:
        """Go forward one step. Returns the next snapshot or None."""
        if self._position >= len(self._history) - 1:
            return None
        self._position += 1
        return self._history[self._position].copy()

    @property
    def can_undo(self) -> bool:
        return self._position > 0

    @property
    def can_redo(self) -> bool:
        return self._position < len(self._history) - 1

    @property
    def depth(self) -> int:
        return len(self._history)

    @property
    def position(self) -> int:
        return self._position

    def begin_restore(self) -> None:
        """Mark that we're restoring — prevents push during restore."""
        self._is_restoring = True

    def end_restore(self) -> None:
        self._is_restoring = False

    def clear(self) -> None:
        self._history.clear()
        self._position = -1
