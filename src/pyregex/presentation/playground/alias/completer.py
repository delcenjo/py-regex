"""AliasCompleter — prompt_toolkit Completer for @alias tokens.

Provides live autocompletion when the user types `@` in the regex input.
Supports fuzzy prefix matching and displays pattern descriptions.
"""

from __future__ import annotations

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

from pyregex.presentation.playground.alias.resolver import AliasResolver


class AliasCompleter(Completer):
    """Autocomplete @alias references from the saved pattern registry."""

    def __init__(self, resolver: AliasResolver):
        self._resolver = resolver

    def get_completions(self, document: Document, complete_event):
        text_before = document.text_before_cursor

        at_pos = text_before.rfind("@")
        if at_pos == -1:
            return

        partial = text_before[at_pos + 1:]

        if " " in partial:
            return

        for name, (pattern, description) in self._resolver.aliases.items():
            if partial == "" or name.lower().startswith(partial.lower()):
                start_position = -(len(partial) + 1)  # +1 for the @ itself
                meta_text = f"{description}" if description else f"Regex: {pattern[:30]}..."

                yield Completion(
                    text=f"@{name}",
                    start_position=start_position,
                    display=f"@{name}",
                    display_meta=meta_text,
                )
