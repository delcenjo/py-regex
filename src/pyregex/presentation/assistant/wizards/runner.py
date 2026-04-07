"""Nebula Wizard Framework — Wizard Runner."""

from __future__ import annotations
from typing import Any

from pyregex.presentation.assistant.core.types import EventType
from pyregex.presentation.assistant.core.session import SessionContext
from pyregex.presentation.assistant.core.events import EventBus
from pyregex.presentation.assistant.wizards.step import WizardStep
from pyregex.presentation.assistant.wizards.renderer import StepRenderer
from pyregex.presentation.assistant.wizards.preview import RegexPreview
from pyregex.presentation.assistant.wizards.branching import BranchingEngine
from pyregex.utils import ansi


class WizardRunner:
    """
    Executes a sequence of wizard steps with full navigation support.

    Features:
    - Sequential step execution with back/cancel
    - Conditional branching between steps
    - Live regex preview after each step
    - Progress indicator
    - Input validation with retry
    """

    def __init__(self, event_bus: EventBus | None = None, show_preview: bool = True):
        self.renderer = StepRenderer()
        self.preview = RegexPreview()
        self.branching = BranchingEngine()
        self._event_bus = event_bus
        self._show_preview = show_preview

    def run(
        self,
        steps: list[WizardStep],
        session: SessionContext,
        wizard_name: str = "",
        partial_builder: Any = None,
    ) -> dict[str, Any]:
        """
        Execute a step sequence. Returns a dict of {step_id: value}.

        Handles back navigation by maintaining a step index that can decrement.
        Handles cancel by returning an empty dict with a 'cancelled' key.
        """
        # Resolve branching
        results: dict[str, Any] = {}
        step_history: list[int] = []  # indices of completed steps

        # Get initial resolved flow
        resolved = self.branching.resolve_flow(steps, results)
        idx = 0

        while idx < len(resolved):
            step = resolved[idx]

            # Show progress
            total = len(resolved)
            self._show_progress(idx + 1, total, wizard_name)

            # Show breadcrumbs
            if session.breadcrumbs:
                print(f"  {ansi.dim(session.breadcrumb_str)}")

            # Render step and get input
            try:
                raw = self.renderer.render(step, results)
            except (KeyboardInterrupt, EOFError):
                results["__cancelled__"] = True
                return results

            # Handle back
            if raw.lower() == "b":
                if step_history:
                    idx = step_history.pop()
                    # Remove the result for the step we're going back to
                    back_step = resolved[idx]
                    results.pop(back_step.id, None)
                    continue
                else:
                    results["__cancelled__"] = True
                    return results

            # Validate input
            is_valid, error_msg = step.validate_input(raw)
            if not is_valid:
                print(f"  {ansi.error(error_msg)}")
                continue  # Re-render same step

            # Transform and store
            value = step.transform_value(raw)
            results[step.id] = value

            # Emit event
            if self._event_bus:
                self._event_bus.emit_simple(
                    EventType.WIZARD_STEP,
                    source="runner",
                    wizard=wizard_name,
                    step=step.id,
                    value=str(value),
                )

            # Run post-step callback
            if step.on_complete:
                try:
                    step.on_complete(value, results)
                except Exception:
                    pass

            # Re-resolve flow (branching may have changed based on this answer)
            old_len = len(resolved)
            resolved = self.branching.resolve_flow(steps, results)

            # Track history for back navigation
            step_history.append(idx)
            idx += 1

            # Adjust index if branching changed the flow length
            if len(resolved) != old_len:
                # Find current step in new flow
                for new_idx, s in enumerate(resolved):
                    if s.id == step.id:
                        idx = new_idx + 1
                        break

        return results

    def _show_progress(self, current: int, total: int, wizard_name: str) -> None:
        """Show step progress indicator."""
        bar_width = 20
        filled = int((current / total) * bar_width) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_width - filled)

        label = wizard_name if wizard_name else "Wizard"
        print(f"\n  {ansi.dim(f'[{bar}] {label} - Paso {current}/{total}')}")
