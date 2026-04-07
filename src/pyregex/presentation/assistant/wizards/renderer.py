"""Nebula Wizard Framework — Step Renderer."""

from __future__ import annotations
from typing import Any

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from pyregex.presentation.assistant.core.types import StepType
from pyregex.presentation.assistant.wizards.step import WizardStep
from pyregex.utils import ansi
from pyregex.i18n import translator as i18n


class StepRenderer:
    """
    Renders wizard steps to the terminal and collects user input.

    Handles different step types (menu, text, confirm, multiselect, number, info)
    and provides consistent styling across all wizards.
    """

    def render(self, step: WizardStep, context: dict[str, Any] | None = None) -> str:
        """Render a step and collect user input. Returns the raw input string."""
        context = context or {}

        # 1. Compact Header
        title = step.title
        # Try to translate if it's a known key
        if "." not in title and not title.isupper(): # Basic check
             translated = i18n.t(f"assistant.wizards.{title.lower().replace(' ', '_')}")
             if translated != f"assistant.wizards.{title.lower().replace(' ', '_')}":
                 title = translated
        
        # Simple, bold title with a decorative separator
        print(f"\n  {ansi.bold(title)}")
        print(f"  {ansi.dim('─' * 40)}")

        # Display help text if present
        if step.help_text:
            print(f"  {ansi.dim(step.help_text)}")

        # Dispatch to type-specific renderer
        if step.step_type == StepType.MENU:
            return self._render_menu(step)
        elif step.step_type == StepType.TEXT:
            return self._render_text(step)
        elif step.step_type == StepType.CONFIRM:
            return self._render_confirm(step)
        elif step.step_type == StepType.MULTISELECT:
            return self._render_multiselect(step)
        elif step.step_type == StepType.NUMBER:
            return self._render_number(step)
        elif step.step_type == StepType.REGEX:
            return self._render_regex(step)
        elif step.step_type == StepType.INFO:
            return self._render_info(step)
        else:
            return self._render_text(step)

    def _render_menu(self, step: WizardStep) -> str:
        """Render a menu selection step."""
        lines = []
        
        # 1. Variants
        for choice in step.choices:
            icon = choice.icon + " " if choice.icon else ""
            disabled = f" ({i18n.t('assistant.wizards.disabled')})" if choice.disabled else ""
            desc = f" - {choice.description}" if choice.description else ""
            key = f"[{choice.key}]"
            
            lines.append(f"  {ansi.info(key)} {icon}{choice.label}{ansi.dim(disabled + desc)}")

        # 2. Back Option
        back_label = i18n.t("assistant.wizards.back")
        back_key = f"[{ansi.FG_MAGENTA}b{ansi.RESET}]" if ansi.SUPPORTS_COLOR else "[b]"
        
        print("\n".join(lines))
        print(f"  {back_key} {ansi.dim(back_label)}")

        keys = [c.key for c in step.choices if not c.disabled] + ["b"]
        completer = WordCompleter(keys, ignore_case=True)
        
        # 3. Prompt (Alone, with a manual newline before)
        print("")
        raw = (
            prompt("> ", completer=completer)
            .strip()
            .lower()
        )

        return raw if raw else (step.default or "")

    def _render_text(self, step: WizardStep) -> str:
        """Render a free-text input step."""
        default_hint = f" [{step.default}]" if step.default else ""
        raw = prompt(f"  {step.prompt_text}{default_hint} ").strip()
        return raw if raw else (step.default or "")

    def _render_confirm(self, step: WizardStep) -> str:
        """Render a yes/no confirmation step."""
        default = step.default or "n"
        hint = "Y/n" if default == "y" else "y/N"
        raw = prompt(f"  ({hint}) ").strip().lower()
        return raw if raw in ("y", "n") else default

    def _render_multiselect(self, step: WizardStep) -> str:
        """Render a multi-selection step."""
        for choice in step.choices:
            print(f"  [{choice.key}] {choice.label}")

        print(f"\n  {ansi.dim('Separate multiple choices with commas')}")
        raw = prompt(f"  {step.prompt_text} ").strip()
        return raw

    def _render_number(self, step: WizardStep) -> str:
        """Render a numeric input step."""
        default_hint = f" [{step.default}]" if step.default else ""
        raw = prompt(f"  {step.prompt_text}{default_hint} ").strip()
        return raw if raw else (step.default or "")

    def _render_regex(self, step: WizardStep) -> str:
        """Render a regex input step with special formatting."""
        print(f"  {ansi.dim('Enter a regular expression:')}")
        raw = prompt("  regex> ").strip()
        return raw

    def _render_info(self, step: WizardStep) -> str:
        """Render an information-only step (no input)."""
        if step.help_text:
            print(f"\n  {step.help_text}")
        prompt(f"  {ansi.dim('Press Enter to continue...')} ")
        return ""
