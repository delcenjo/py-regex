"""Nebula Wizard Framework — Step Model."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from pyregex.presentation.assistant.core.types import StepType, Choice


@dataclass
class WizardStep:
    """
    A single step in a wizard flow.

    Steps are declarative: define what to show, how to validate,
    and what to do — the WizardRunner handles execution.
    """

    id: str
    title: str
    step_type: StepType = StepType.MENU

    choices: list[Choice] = field(default_factory=list)
    prompt_text: str = "> "
    help_text: str = ""

    default: Optional[str] = None
    validator: Optional[Callable[[str], tuple[bool, str]]] = None
    required: bool = True

    condition: Optional[Callable[[dict[str, Any]], bool]] = None
    transform: Optional[Callable[[str], Any]] = None
    on_complete: Optional[Callable[[Any, dict[str, Any]], None]] = None

    def should_show(self, context: dict[str, Any]) -> bool:
        """Check if this step should be shown based on its condition."""
        if self.condition is None:
            return True
        return self.condition(context)

    def validate_input(self, value: str) -> tuple[bool, str]:
        """Validate user input. Returns (is_valid, error_message)."""
        if self.required and not value.strip():
            return False, "This field is required"
        if self.validator:
            return self.validator(value)
        return True, ""

    def transform_value(self, raw: str) -> Any:
        """Transform raw input to stored value."""
        if self.transform:
            return self.transform(raw)
        return raw


def menu_step(
    id: str, title: str, choices: list[tuple[str, str]], **kwargs
) -> WizardStep:
    """Convenience factory for menu steps."""
    return WizardStep(
        id=id,
        title=title,
        step_type=StepType.MENU,
        choices=[Choice(key=k, label=l) for k, l in choices],
        **kwargs,
    )


def text_step(id: str, title: str, prompt: str = "> ", **kwargs) -> WizardStep:
    """Convenience factory for text input steps."""
    return WizardStep(
        id=id, title=title, step_type=StepType.TEXT, prompt_text=prompt, **kwargs
    )


def confirm_step(id: str, title: str, **kwargs) -> WizardStep:
    """Convenience factory for yes/no confirmation steps."""
    return WizardStep(
        id=id,
        title=title,
        step_type=StepType.CONFIRM,
        choices=[Choice(key="y", label="Yes"), Choice(key="n", label="No")],
        default="n",
        **kwargs,
    )


def number_step(id: str, title: str, **kwargs) -> WizardStep:
    """Convenience factory for numeric input steps."""

    def validate_number(val: str) -> tuple[bool, str]:
        try:
            int(val)
            return True, ""
        except ValueError:
            return False, "Please enter a valid number"

    return WizardStep(
        id=id,
        title=title,
        step_type=StepType.NUMBER,
        validator=validate_number,
        transform=lambda v: int(v),
        **kwargs,
    )
