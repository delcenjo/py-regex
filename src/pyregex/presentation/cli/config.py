from __future__ import annotations
import argparse
from typing import TYPE_CHECKING, Any

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class ConfigCommand(BaseCommand):
    """Manages the PyRegex configuration."""

    @property
    def name(self) -> str:
        return "config"

    @property
    def help(self) -> str:
        return "Manage PyRegex configuration"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument(
            "--set", nargs=2, metavar=("KEY", "VALUE"), help="Set a config value"
        )
        parser.add_argument("--get", metavar="KEY", help="Get a config value")
        parser.add_argument("--reset", action="store_true", help="Reset to defaults")
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        if args.reset:
            cli.config_repo.reset()
            print(ansi.success("Configuration reset to defaults."))
            return 0

        if args.set:
            key, val = args.set
            cli.config_repo.update(key, val)
            print(ansi.success(f"Updated {key} to {val}"))
            return 0

        if args.get:
            val = cli.config_repo.get(args.get)
            print(f"{ansi.label(args.get + ':')} {val}")
            return 0

        # Default: show all
        print(f"\n{ansi.bold('Current Configuration:')}")
        for k, v in cli.config.__dict__.items():
            print(f" {k}: {v}")

        return 0
