"""Playground — Event System (pub/sub).

Decoupled communication between playground components.
Events are typed and carry arbitrary data payloads.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum
import time


class PlaygroundEvent(Enum):
    """All playground events."""

    # Lifecycle
    APP_START = "app_start"
    APP_EXIT = "app_exit"
    APP_RESIZE = "app_resize"

    # Regex
    REGEX_CHANGED = "regex_changed"
    REGEX_COMPILED = "regex_compiled"
    REGEX_ERROR = "regex_error"
    REGEX_CLEARED = "regex_cleared"

    # Input
    INPUT_CHANGED = "input_changed"
    INPUT_LOADED = "input_loaded"
    INPUT_CLEARED = "input_cleared"

    # Matching
    MATCH_STARTED = "match_started"
    MATCH_COMPLETED = "match_completed"
    MATCH_TIMEOUT = "match_timeout"
    MATCH_NONE = "match_none"

    # Analysis
    COMPLEXITY_UPDATED = "complexity_updated"
    WARNING_DETECTED = "warning_detected"
    EXPLANATION_UPDATED = "explanation_updated"

    # UI
    PANEL_TOGGLE = "panel_toggle"
    PANEL_FOCUS = "panel_focus"
    THEME_CHANGED = "theme_changed"
    LAYOUT_CHANGED = "layout_changed"

    # Actions
    PATTERN_SAVED = "pattern_saved"
    PATTERN_LOADED = "pattern_loaded"
    PATTERN_EXPORTED = "pattern_exported"
    UNDO = "undo"
    REDO = "redo"

    # Debug
    DEBUG_STEP = "debug_step"
    DEBUG_START = "debug_start"
    DEBUG_END = "debug_end"

    # Flags
    FLAG_TOGGLED = "flag_toggled"

    # Replace
    REPLACE_CHANGED = "replace_changed"
    REPLACE_APPLIED = "replace_applied"

    # Performance
    PERF_UPDATED = "perf_updated"
    REDOS_DETECTED = "redos_detected"


@dataclass
class EventPayload:
    """Payload for an event."""

    event: PlaygroundEvent
    timestamp: float = field(default_factory=time.time)
    source: str = ""
    data: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Simple pub/sub event bus for playground components."""

    def __init__(self):
        self._handlers: dict[PlaygroundEvent, list[Callable]] = {}
        self._global_handlers: list[Callable] = []
        self._event_log: list[EventPayload] = []
        self._max_log: int = 200
        self._muted: bool = False

    def on(self, event: PlaygroundEvent, handler: Callable) -> None:
        """Subscribe to a specific event."""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def on_any(self, handler: Callable) -> None:
        """Subscribe to ALL events."""
        self._global_handlers.append(handler)

    def off(self, event: PlaygroundEvent, handler: Callable) -> None:
        """Unsubscribe from an event."""
        if event in self._handlers:
            self._handlers[event] = [h for h in self._handlers[event] if h != handler]

    def emit(self, event: PlaygroundEvent, source: str = "", **data) -> None:
        """Emit an event to all subscribers."""
        if self._muted:
            return

        payload = EventPayload(event=event, source=source, data=data)

        # Log
        self._event_log.append(payload)
        if len(self._event_log) > self._max_log:
            self._event_log = self._event_log[-self._max_log :]

        # Notify specific handlers
        for handler in self._handlers.get(event, []):
            try:
                handler(payload)
            except Exception:
                pass

        # Notify global handlers
        for handler in self._global_handlers:
            try:
                handler(payload)
            except Exception:
                pass

    def mute(self) -> None:
        """Temporarily suppress all events."""
        self._muted = True

    def unmute(self) -> None:
        self._muted = False

    @property
    def log(self) -> list[EventPayload]:
        return self._event_log

    def clear(self) -> None:
        self._handlers.clear()
        self._global_handlers.clear()
        self._event_log.clear()

    @property
    def handler_count(self) -> int:
        return sum(len(v) for v in self._handlers.values()) + len(self._global_handlers)
