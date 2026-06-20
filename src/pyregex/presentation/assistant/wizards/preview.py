"""Nebula Wizard Framework — Live Regex Preview."""

from __future__ import annotations
import re

from pyregex.utils import ansi


class RegexPreview:
    """
    Provides real-time regex preview during wizard execution.

    After each step, shows:
    - Current regex pattern (partial or complete)
    - Match examples (if available)
    - Complexity indicator
    """

    def show_pattern(self, pattern: str) -> None:
        """Display the current regex pattern."""
        print(f"\n  {ansi.dim('Regex parcial:')} {ansi.regex_display(pattern)}")

        try:
            re.compile(pattern)
            print(f"  {ansi.success('')} Patrón válido")
        except re.error as e:
            print(f"  {ansi.error('')} Patrón inválido: {e}")

    def show_test(
        self, pattern: str, examples: list[str], non_examples: list[str] | None = None
    ) -> None:
        """Show match results against example data."""
        non_examples = non_examples or []

        try:
            rx = re.compile(pattern)
        except re.error:
            return

        print(f"\n  {ansi.bold('Vista previa:')}")

        for text in examples[:4]:
            match = rx.search(text)
            if match:
                print(f"    {ansi.success('')} {text}")
            else:
                print(f"    {ansi.warning('~')} {text} {ansi.dim('(no match)')}")

        for text in non_examples[:3]:
            match = rx.search(text)
            if match:
                print(f"    {ansi.error('')} {text} {ansi.dim('(unexpected match)')}")
            else:
                print(
                    f"    {ansi.success('')} {text} {ansi.dim('(correctly rejected)')}"
                )

    def show_complexity(self, pattern: str) -> None:
        """Show basic complexity indicator."""
        length = len(pattern)
        groups = pattern.count("(")
        alternations = pattern.count("|")

        if length > 200 or groups > 10:
            level = ansi.error("█████ Complejo")
        elif length > 100 or groups > 5:
            level = ansi.warning("███░░ Medio")
        else:
            level = ansi.success("█░░░░ Simple")

        print(f"  {ansi.dim('Complejidad:')} {level} ({length} chars, {groups} groups)")
