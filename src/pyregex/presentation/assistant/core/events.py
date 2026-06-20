"""Nebula Assistant Engine — Event Bus."""

from __future__ import annotations
from typing import Callable, Any
from collections import defaultdict

from pyregex.presentation.assistant.core.types import Event, EventType


class EventBus:
    """
    Publish/Subscribe event bus for lifecycle hooks.

    Allows modules, middleware, and UI components to react to system events
    without tight coupling. Supports prioritized listeners and one-shot subscriptions.
    """

    def __init__(self):
        self._listeners: dict[EventType, list[tuple[int, Callable[[Event], None]]]] = (
            defaultdict(list)
        )
        self._one_shot: dict[EventType, list[Callable[[Event], None]]] = defaultdict(
            list
        )
        self._history: list[Event] = []
        self._max_history = 500

    def on(
        self,
        event_type: EventType,
        callback: Callable[[Event], None],
        priority: int = 0,
    ) -> None:
        """Register a permanent listener for an event type."""
        self._listeners[event_type].append((priority, callback))
        self._listeners[event_type].sort(key=lambda x: x[0], reverse=True)

    def once(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Register a one-shot listener that fires only once."""
        self._one_shot[event_type].append(callback)

    def off(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Unregister a listener."""
        self._listeners[event_type] = [
            (p, cb) for p, cb in self._listeners[event_type] if cb != callback
        ]
        self._one_shot[event_type] = [
            cb for cb in self._one_shot[event_type] if cb != callback
        ]

    def emit(self, event: Event) -> None:
        """Emit an event to all registered listeners."""
        # Record in history
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        # Fire permanent listeners
        for _, callback in self._listeners.get(event.type, []):
            try:
                callback(event)
            except Exception:
                pass  # Never let a listener break the emitter

        # Fire one-shot listeners
        for callback in self._one_shot.pop(event.type, []):
            try:
                callback(event)
            except Exception:
                pass

    def emit_simple(self, event_type: EventType, source: str = "", **data: Any) -> None:
        """Convenience: emit an event without constructing the Event object."""
        self.emit(Event(type=event_type, source=source, data=data))

    def get_history(
        self, event_type: EventType | None = None, limit: int = 50
    ) -> list[Event]:
        """Retrieve event history, optionally filtered by type."""
        if event_type:
            filtered = [e for e in self._history if e.type == event_type]
        else:
            filtered = list(self._history)
        return filtered[-limit:]

    def clear(self) -> None:
        """Clear all listeners and history."""
        self._listeners.clear()
        self._one_shot.clear()
        self._history.clear()

    @property
    def listener_count(self) -> int:
        """Total number of registered listeners."""
        return sum(len(v) for v in self._listeners.values()) + sum(
            len(v) for v in self._one_shot.values()
        )
