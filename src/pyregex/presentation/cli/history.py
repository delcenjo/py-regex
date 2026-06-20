from __future__ import annotations
import argparse
from typing import TYPE_CHECKING, Any

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class HistoryCommand(BaseCommand):
    """Manages the regex command history."""

    @property
    def name(self) -> str:
        return "history"

    @property
    def help(self) -> str:
        return "Manage command history"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument(
            "-l", "--limit", type=int, default=10, help="Number of entries to show"
        )
        parser.add_argument("-c", "--clear", action="store_true", help="Clear history")
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        if args.clear:
            cli.history_repo.clear()
            print(ansi.success("History cleared."))
            return 0

        entries = cli.history_repo.get_recent(limit=args.limit)
        if not entries:
            print(ansi.info("History is empty."))
            return 0

        print(f"\n{ansi.bold('Recent Commands:')}")
        for i, entry in enumerate(entries, 1):
            print(
                f" {i}. {ansi.regex_display(entry.pattern)} {ansi.dim('(' + entry.context + ')')}"
            )

        return 0
