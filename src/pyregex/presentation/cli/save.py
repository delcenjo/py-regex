from __future__ import annotations
import argparse
from typing import TYPE_CHECKING, Any
from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi
from pyregex.i18n import translator as i18n

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class SaveCommand(BaseCommand):
    """Saves a regex pattern to the persistent registry."""

    @property
    def name(self) -> str:
        return "save"

    @property
    def help(self) -> str:
        return "Save a regex pattern to the persistent registry"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument(
            "-n", "--name", required=True, help="Short name for the pattern"
        )
        parser.add_argument(
            "-p", "--pattern", required=True, help="The regex pattern string"
        )
        parser.add_argument(
            "-d", "--description", help="Brief description of what it does"
        )
        parser.add_argument("--tags", help="Comma-separated list of tags")
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        tags = []
        if args.tags:
            tags = [t.strip().lower() for t in args.tags.split(",") if t.strip()]

        success, errors, p = cli.registry_system.save(
            name=args.name,
            pattern=args.pattern,
            description=args.description or "",
            tags=tags,
        )

        if not success:
            for err in errors:
                print(ansi.error(err))
            return 1

        print(ansi.success(i18n.t("common.saved", name=args.name)))

        if p.metadata.category != "uncategorized":
            print(
                f"{ansi.bold('  Auto-categorized as:')} {ansi.info(p.metadata.category)}"
            )
        if p.metadata.tags:
            print(
                f"{ansi.bold('  Auto-tagged as:')} {ansi.info(', '.join(p.metadata.tags))}"
            )

        return 0
