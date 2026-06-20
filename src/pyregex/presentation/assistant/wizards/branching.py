"""Nebula Wizard Framework — Conditional Step Branching."""

from __future__ import annotations
from typing import Any, Callable

from pyregex.presentation.assistant.wizards.step import WizardStep


class BranchingEngine:
    """
    Manages conditional step flow within a wizard.

    Supports:
    - Skip conditions (don't show step if condition is false)
    - Branch-on-value (show different next steps based on answer)
    - Step groups (show a block of steps based on a condition)
    - Loop-back (repeat a step group)
    """

    def __init__(self):
        self._branches: dict[str, dict[str, list[WizardStep]]] = {}
        self._skip_conditions: dict[str, Callable[[dict], bool]] = {}
        self._step_groups: dict[str, list[WizardStep]] = {}

    def add_branch(
        self, step_id: str, value: str, extra_steps: list[WizardStep]
    ) -> None:
        """
        When step_id produces value, inject extra_steps into the flow.
        Example: if email type is "corp", add domain selection steps.
        """
        if step_id not in self._branches:
            self._branches[step_id] = {}
        self._branches[step_id][value] = extra_steps

    def add_skip_condition(
        self, step_id: str, condition: Callable[[dict], bool]
    ) -> None:
        """Skip a step when condition returns True."""
        self._skip_conditions[step_id] = condition

    def add_step_group(self, group_id: str, steps: list[WizardStep]) -> None:
        """Register a named group of steps that can be injected via branching."""
        self._step_groups[group_id] = steps

    def should_skip(self, step_id: str, context: dict[str, Any]) -> bool:
        """Check if a step should be skipped."""
        if step_id in self._skip_conditions:
            return self._skip_conditions[step_id](context)
        return False

    def get_branch_steps(self, step_id: str, value: str) -> list[WizardStep]:
        """Get extra steps injected after a specific step+value combination."""
        return self._branches.get(step_id, {}).get(value, [])

    def get_group(self, group_id: str) -> list[WizardStep]:
        """Retrieve a named step group."""
        return self._step_groups.get(group_id, [])

    def resolve_flow(
        self, steps: list[WizardStep], results: dict[str, Any]
    ) -> list[WizardStep]:
        """
        Resolve the complete step flow by evaluating all branches and conditions.
        Returns the final ordered list of steps to execute.
        """
        resolved = []

        for step in steps:
            # Check skip condition (step-level)
            if self.should_skip(step.id, results):
                continue

            # Check step's own condition
            if not step.should_show(results):
                continue

            resolved.append(step)

            # Check if this step's result triggers additional steps
            if step.id in results and step.id in self._branches:
                value = str(results[step.id])
                branch_steps = self.get_branch_steps(step.id, value)
                for bs in branch_steps:
                    if bs.should_show(results):
                        resolved.append(bs)

        return resolved
