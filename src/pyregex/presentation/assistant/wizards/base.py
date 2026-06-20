"""Nebula Wizard Framework — Base Wizard ABC."""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

from pyregex.presentation.assistant.core.types import WizardResult
from pyregex.presentation.assistant.core.session import SessionContext
from pyregex.presentation.assistant.wizards.step import WizardStep
from pyregex.presentation.assistant.wizards.runner import WizardRunner
from pyregex.presentation.assistant.wizards.preview import RegexPreview
from pyregex.presentation.assistant.wizards.finalizer import WizardFinalizer
from pyregex.presentation.assistant.wizards.branching import BranchingEngine
from pyregex.utils import ansi


class BaseWizard(ABC):
    """
    Abstract base class for all regex generation wizards.

    Subclasses define steps declaratively and implement build_pattern()
    to convert collected answers into a regex pattern.

    Usage:
        class EmailWizard(BaseWizard):
            name = "email_wizard"
            display_name = "Email Address"

            def define_steps(self) -> list[WizardStep]:
                return [
                    menu_step("type", "Email Type", [("std", "Standard"), ...]),
                    text_step("domain", "Custom Domain", condition=lambda ctx: ctx["type"] == "custom"),
                ]

            def build_pattern(self, answers: dict) -> str:
                if answers["type"] == "std":
                    return r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}'
                ...
    """

    name: str = ""
    display_name: str = ""
    description: str = ""
    icon: str = ""
    tags: list[str] = []

    def __init__(self, cli: Any = None, session: SessionContext | None = None):
        self.cli = cli
        self._session = session
        self._runner = WizardRunner()
        self._preview = RegexPreview()

    @abstractmethod
    def define_steps(self) -> list[WizardStep]:
        """Define the wizard's step sequence."""
        ...

    @abstractmethod
    def build_pattern(self, answers: dict[str, Any]) -> str:
        """Build the final regex from collected answers."""
        ...

    def get_examples(self, answers: dict[str, Any], pattern: str) -> list[str]:
        """Override to provide match examples."""
        return []

    def get_non_examples(self, answers: dict[str, Any], pattern: str) -> list[str]:
        """Override to provide non-match examples."""
        return []

    def setup_branching(self, engine: BranchingEngine) -> None:
        """Override to define conditional branching rules."""
        pass

    def validate_pattern(self, pattern: str) -> tuple[bool, str]:
        """Validate the pattern compiles as a valid regex. Override for custom validation."""
        import re

        try:
            re.compile(pattern)
            return True, ""
        except re.error as e:
            return False, str(e)

    def execute(self, session: SessionContext | None = None) -> WizardResult:
        """Run the wizard: collect answers, build and validate the pattern, show preview, finalize."""
        session = session or self._session or SessionContext()

        steps = self.define_steps()
        self.setup_branching(self._runner.branching)

        print(f"\n{'━' * 55}")
        print(f"  {self.icon} {ansi.bold(self.display_name or self.name)}")
        if self.description:
            print(f"  {ansi.dim(self.description)}")
        print(f"{'━' * 55}")

        answers = self._runner.run(
            steps=steps,
            session=session,
            wizard_name=self.display_name or self.name,
        )

        if answers.get("__cancelled__"):
            return WizardResult(
                pattern="", builder_name=self.name, cancelled=True, success=False
            )

        try:
            pattern = self.build_pattern(answers)
        except Exception as e:
            print(ansi.error(f"Error building pattern: {e}"))
            return WizardResult(
                pattern="", builder_name=self.name, success=False, error=str(e)
            )

        is_valid, error = self.validate_pattern(pattern)
        if not is_valid:
            print(ansi.error(f"Generated invalid pattern: {error}"))
            return WizardResult(
                pattern=pattern, builder_name=self.name, success=False, error=error
            )

        examples = self.get_examples(answers, pattern)
        non_examples = self.get_non_examples(answers, pattern)

        result = WizardResult(
            pattern=pattern,
            builder_name=self.name,
            tags=list(self.tags),
            description=self.description,
            step_results={},
            metadata=answers,
            examples=examples,
            non_examples=non_examples,
            success=True,
        )

        self._preview.show_pattern(pattern)
        if examples or non_examples:
            self._preview.show_test(pattern, examples, non_examples)
        self._preview.show_complexity(pattern)

        # individual actions handle missing cli
        finalizer = WizardFinalizer(self.cli)
        result = finalizer.run(result, session)

        return result
