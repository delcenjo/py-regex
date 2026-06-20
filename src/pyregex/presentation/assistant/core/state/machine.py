"""Nebula Assistant Engine — Finite State Machine."""

from __future__ import annotations
from typing import Callable, Optional
from dataclasses import dataclass

from pyregex.presentation.assistant.core.types import SessionState


@dataclass
class Transition:
    """A single state transition rule."""

    from_state: SessionState
    to_state: SessionState
    trigger: str
    guard: Optional[Callable[[dict], bool]] = None
    action: Optional[Callable[[dict], None]] = None
    description: str = ""


class StateMachine:
    """
    Finite State Machine for controlling assistant navigation flow.

    Manages valid transitions between states and enforces guards
    (preconditions) before allowing transitions. Each transition can
    optionally fire an action callback.

    States: IDLE → BROWSING → IN_MODULE → IN_WIZARD → PREVIEWING → FINALIZING
    """

    def __init__(self, initial_state: SessionState = SessionState.IDLE):
        self._state = initial_state
        self._transitions: list[Transition] = []
        self._state_history: list[SessionState] = []
        self._on_enter_callbacks: dict[SessionState, list[Callable]] = {}
        self._on_exit_callbacks: dict[SessionState, list[Callable]] = {}

        # Setup default transitions
        self._setup_defaults()

    @property
    def state(self) -> SessionState:
        return self._state

    @property
    def history(self) -> list[SessionState]:
        return list(self._state_history)

    def add_transition(self, transition: Transition) -> None:
        """Register a new transition rule."""
        self._transitions.append(transition)

    def on_enter(self, state: SessionState, callback: Callable) -> None:
        """Register a callback for when entering a state."""
        if state not in self._on_enter_callbacks:
            self._on_enter_callbacks[state] = []
        self._on_enter_callbacks[state].append(callback)

    def on_exit(self, state: SessionState, callback: Callable) -> None:
        """Register a callback for when leaving a state."""
        if state not in self._on_exit_callbacks:
            self._on_exit_callbacks[state] = []
        self._on_exit_callbacks[state].append(callback)

    def can_trigger(self, trigger: str, context: dict | None = None) -> bool:
        """Check if a trigger can fire from the current state."""
        ctx = context or {}
        for t in self._transitions:
            if t.from_state == self._state and t.trigger == trigger:
                if t.guard is None or t.guard(ctx):
                    return True
        return False

    def trigger(self, trigger_name: str, context: dict | None = None) -> bool:
        """
        Attempt to fire a trigger. Returns True if transition succeeded.
        """
        ctx = context or {}
        for t in self._transitions:
            if t.from_state == self._state and t.trigger == trigger_name:
                if t.guard and not t.guard(ctx):
                    continue

                # Exit callbacks
                for cb in self._on_exit_callbacks.get(self._state, []):
                    cb(ctx)

                # Record history
                self._state_history.append(self._state)

                # Transition
                old_state = self._state
                self._state = t.to_state

                # Run transition action
                if t.action:
                    t.action(ctx)

                # Enter callbacks
                for cb in self._on_enter_callbacks.get(self._state, []):
                    cb(ctx)

                return True

        return False

    def force_state(self, state: SessionState) -> None:
        """Force a state change without checks (for error recovery)."""
        self._state_history.append(self._state)
        self._state = state

    def reset(self) -> None:
        """Reset to initial state."""
        self._state = SessionState.IDLE
        self._state_history.clear()

    def get_available_triggers(self) -> list[str]:
        """Get all triggers valid from the current state."""
        return list(
            set(t.trigger for t in self._transitions if t.from_state == self._state)
        )

    def _setup_defaults(self) -> None:
        """Define the standard flow transitions."""
        transitions = [
            # IDLE → BROWSING (user launched assistant)
            Transition(
                SessionState.IDLE,
                SessionState.BROWSING,
                "start",
                description="User launches the assistant",
            ),
            # BROWSING → IN_MODULE (user selects a category/module)
            Transition(
                SessionState.BROWSING,
                SessionState.IN_MODULE,
                "select_module",
                description="User selects a module or category",
            ),
            # IN_MODULE → IN_WIZARD (user selects a wizard)
            Transition(
                SessionState.IN_MODULE,
                SessionState.IN_WIZARD,
                "start_wizard",
                description="User starts a wizard",
            ),
            # BROWSING → IN_WIZARD (direct shortcut to wizard)
            Transition(
                SessionState.BROWSING,
                SessionState.IN_WIZARD,
                "start_wizard",
                description="User uses a direct shortcut",
            ),
            # IN_WIZARD → PREVIEWING (wizard completes, show preview)
            Transition(
                SessionState.IN_WIZARD,
                SessionState.PREVIEWING,
                "preview",
                description="Wizard generates pattern, show preview",
            ),
            # PREVIEWING → FINALIZING (user proceeds to actions)
            Transition(
                SessionState.PREVIEWING,
                SessionState.FINALIZING,
                "finalize",
                description="User moves to save/test/edit actions",
            ),
            # FINALIZING → BROWSING (user finishes or starts new)
            Transition(
                SessionState.FINALIZING,
                SessionState.BROWSING,
                "done",
                description="Action complete, return to browsing",
            ),
            # Back transitions
            Transition(
                SessionState.IN_MODULE,
                SessionState.BROWSING,
                "back",
                description="Back from module to browsing",
            ),
            Transition(
                SessionState.IN_WIZARD,
                SessionState.IN_MODULE,
                "back",
                description="Back from wizard to module",
            ),
            Transition(
                SessionState.PREVIEWING,
                SessionState.IN_WIZARD,
                "back",
                description="Back from preview to wizard",
            ),
            Transition(
                SessionState.FINALIZING,
                SessionState.PREVIEWING,
                "back",
                description="Back from finalize to preview",
            ),
            # Cancel (always goes to browsing)
            Transition(
                SessionState.IN_WIZARD,
                SessionState.BROWSING,
                "cancel",
                description="Cancel wizard",
            ),
            Transition(
                SessionState.PREVIEWING,
                SessionState.BROWSING,
                "cancel",
                description="Cancel from preview",
            ),
            Transition(
                SessionState.FINALIZING,
                SessionState.BROWSING,
                "cancel",
                description="Cancel from finalize",
            ),
            # Help (from any state)
            Transition(SessionState.BROWSING, SessionState.HELP, "help"),
            Transition(SessionState.IN_MODULE, SessionState.HELP, "help"),
            Transition(SessionState.IN_WIZARD, SessionState.HELP, "help"),
            # Return from help
            Transition(SessionState.HELP, SessionState.BROWSING, "back"),
            Transition(SessionState.HELP, SessionState.IN_MODULE, "back"),
            Transition(SessionState.HELP, SessionState.IN_WIZARD, "back"),
            # Error recovery
            Transition(
                SessionState.ERROR,
                SessionState.BROWSING,
                "recover",
                description="Recover from error",
            ),
            Transition(
                SessionState.ERROR,
                SessionState.IDLE,
                "reset",
                description="Full reset from error",
            ),
            # Catalog Browsing
            Transition(
                SessionState.IDLE,
                SessionState.BROWSING_CATALOG,
                "create",
            ),
            Transition(
                SessionState.BROWSING,
                SessionState.BROWSING_CATALOG,
                "create",
            ),
            Transition(
                SessionState.BROWSING_CATALOG,
                SessionState.BROWSING_CATALOG,
                "menu_select",
            ),
            Transition(
                SessionState.BROWSING_CATALOG,
                SessionState.IN_WIZARD,
                "start_wizard",
            ),
            Transition(
                SessionState.BROWSING_CATALOG,
                SessionState.BROWSING,
                "back",
            ),
        ]

        for t in transitions:
            self.add_transition(t)
