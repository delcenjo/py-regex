from __future__ import annotations
import argparse
import sys
import re
from typing import TYPE_CHECKING, Any

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class ReplaceCommand(BaseCommand):
    """Replaces matches in text using a regex pattern and replacement string."""

    @property
    def name(self) -> str:
        return "replace"

    @property
    def help(self) -> str:
        return "Replace matches in text using a pattern and replacement"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument(
            "-p", "--pattern", required=True, help="Pattern to search for"
        )
        parser.add_argument(
            "-r", "--replacement", required=True, help="Replacement string"
        )
        parser.add_argument("-t", "--text", help="Text to replace in")
        parser.add_argument("-f", "--file", help="File to replace in")
        parser.add_argument("-i", "--ignore-case", action="store_true")
        parser.add_argument(
            "--inplace", action="store_true", help="Modify file in place"
        )
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
        new_content = re.sub(args.pattern, args.replacement, content, flags=flags)

        if args.inplace and args.file:
            try:
                with open(args.file, "w") as f:
                    f.write(new_content)
                print(ansi.success(f"Updated {args.file}"))
            except Exception as e:
                print(ansi.error(f"Failed to update file: {e}"))
                return 1
        else:
            print(new_content)

        return 0
