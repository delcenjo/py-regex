"""Shell REPL for PyRegex."""

from __future__ import annotations
import os
import shlex
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from .completer import PyRegexCompleter
from pyregex.utils import ansi


class PyRegexShell:
    """REPL for interactive PyRegex session."""

    def __init__(self, cli_instance):
        self.cli = cli_instance
        self.history_path = Path.home() / ".pyregex" / "shell_history"
        self.history_path.parent.mkdir(parents=True, exist_ok=True)

    def run(self):
        completer = PyRegexCompleter(self.cli)

        session = PromptSession(
            history=FileHistory(str(self.history_path)),
            completer=completer,
            auto_suggest=AutoSuggestFromHistory(),
            complete_while_typing=True,
        )

        ansi.print_banner("PyRegex Interactive Shell")
        print(f"Type {ansi.bold('exit')} or press Ctrl+D to quit.")

        while True:
            try:
                text = session.prompt("pyregex> ").strip()
                if not text:
                    continue

                if text.lower() in ["exit", "quit"]:
                    break

                if text.lower() == "clear":
                    os.system("clear" if os.name == "posix" else "cls")
                    continue

                # Parse and run via the main CLI instance
                try:
                    args = shlex.split(text)
                    self.cli.run(args)
                except SystemExit:
                    # Caught from PyRegexParser (e.g. --help or error)
                    # We just continue to the next prompt
                    pass
                except Exception as e:
                    print(ansi.error(f"Execution failed: {e}"))

            except KeyboardInterrupt:
                continue
            except EOFError:
                break

        print("\nGoodbye!")
