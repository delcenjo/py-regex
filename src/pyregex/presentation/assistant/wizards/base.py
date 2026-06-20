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

    # Subclass must define these
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

    # ── Abstract Methods ─────────────────────────────────────────────

    @abstractmethod
    def define_steps(self) -> list[WizardStep]:
        """Define the wizard's step sequence. Must be implemented by subclass."""
        ...

    @abstractmethod
    def build_pattern(self, answers: dict[str, Any]) -> str:
        """Build the final regex from collected answers. Must be implemented by subclass."""
        ...

    # ── Optional Overrides ───────────────────────────────────────────

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
        """Override for custom pattern validation."""
        import re

        try:
            re.compile(pattern)
            return True, ""
        except re.error as e:
            return False, str(e)

    # ── Execution ────────────────────────────────────────────────────

    def execute(self, session: SessionContext | None = None) -> WizardResult:
        """
        Main execution flow:
        1. Define steps
        2. Setup branching
        3. Run steps via WizardRunner
        4. Build pattern from answers
        5. Show result via Finalizer
        """
        session = session or self._session or SessionContext()

        # 1. Define steps
        steps = self.define_steps()

        # 2. Setup branching
        self.setup_branching(self._runner.branching)

        # 3. Show wizard header
        print(f"\n{'━' * 55}")
        print(f"  {self.icon} {ansi.bold(self.display_name or self.name)}")
        if self.description:
            print(f"  {ansi.dim(self.description)}")
        print(f"{'━' * 55}")

        # 4. Run steps
        answers = self._runner.run(
            steps=steps,
            session=session,
            wizard_name=self.display_name or self.name,
        )

        # Check for cancellation
        if answers.get("__cancelled__"):
            return WizardResult(
                pattern="", builder_name=self.name, cancelled=True, success=False
            )

        # 5. Build pattern
        try:
            pattern = self.build_pattern(answers)
        except Exception as e:
            print(ansi.error(f"Error building pattern: {e}"))
            return WizardResult(
                pattern="", builder_name=self.name, success=False, error=str(e)
            )

        # 6. Validate pattern
        is_valid, error = self.validate_pattern(pattern)
        if not is_valid:
            print(ansi.error(f"Generated invalid pattern: {error}"))
            return WizardResult(
                pattern=pattern, builder_name=self.name, success=False, error=error
            )

        # 7. Get examples
        examples = self.get_examples(answers, pattern)
        non_examples = self.get_non_examples(answers, pattern)

        # 8. Build result
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

        # 9. Show preview
        self._preview.show_pattern(pattern)
        if examples or non_examples:
            self._preview.show_test(pattern, examples, non_examples)
        self._preview.show_complexity(pattern)

        # 10. Run finalizer (always run — individual actions handle missing cli)
        finalizer = WizardFinalizer(self.cli)
        result = finalizer.run(result, session)

        return result
