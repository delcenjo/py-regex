from __future__ import annotations
import argparse
import sys
import re
from typing import TYPE_CHECKING, Any

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class ExtractCommand(BaseCommand):
    """Extracts matches from text using a regex pattern."""

    @property
    def name(self) -> str:
        return "extract"

    @property
    def help(self) -> str:
        return "Extract matches from text using a pattern"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument(
            "-p", "--pattern", required=True, help="Pattern to extract with"
        )
        parser.add_argument("-t", "--text", help="Text to extract from")
        parser.add_argument("-f", "--file", help="File to extract from")
        parser.add_argument("-i", "--ignore-case", action="store_true")
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        content = ""
        if args.text:
            content = args.text
        elif args.file:
            try:
                with open(args.file, "r") as f:
                    content = f.read()
            except Exception as e:
                print(ansi.error(f"Failed to read file: {e}"))
                return 1
        elif not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            print(ansi.error("Either --text, --file or piped input is required."))
            return 1

        flags = re.IGNORECASE if args.ignore_case else 0
        matches = re.findall(args.pattern, content, flags=flags)

        if not matches:
            print(ansi.info("No matches found."))
            return 0

        print(f"\n{ansi.bold('Extracted Matches:')}")
        for i, match in enumerate(matches, 1):
            if isinstance(match, tuple):
                print(f" {i}. {', '.join(match)}")
            else:
                print(f" {i}. {match}")

        return 0
