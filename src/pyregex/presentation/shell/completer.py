from __future__ import annotations
from prompt_toolkit.completion import Completer, Completion
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from pyregex.presentation.cli.cli import PyRegexCLI


class PyRegexCompleter(Completer):
    """Custom completer for the PyRegex interactive shell."""

    def __init__(self, cli: PyRegexCLI):
        self.cli = cli

    def get_completions(self, document, complete_event) -> Iterable[Completion]:
        text = document.text_before_cursor.lstrip()
        if not text:
            for cmd in self.cli.dispatcher.commands.keys():
                yield Completion(cmd, start_position=0)
            return

        parts = text.split()
        if len(parts) <= 1 and not text.endswith(" "):
            word = parts[0] if parts else ""
            for cmd in self.cli.dispatcher.commands.keys():
                if cmd.startswith(word):
                    yield Completion(cmd, start_position=-len(word))
        else:
            # Completing arguments/patterns (simplified for now)
            # Future: add pattern-specific completion from registry
            pass
