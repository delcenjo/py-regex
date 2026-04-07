from __future__ import annotations
import argparse
import json
import yaml
from typing import TYPE_CHECKING, Any

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class ExportCommand(BaseCommand):
    """Exports patterns from the repository."""

    @property
    def name(self) -> str:
        return "export"

    @property
    def help(self) -> str:
        return "Export patterns to JSON, YAML, or ENV"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument(
            "-f", "--format", choices=["json", "yaml", "env"], default="json"
        )
        parser.add_argument("-o", "--output", help="File to export to")
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        patterns = cli.pattern_repo.get_all()
        if not patterns:
            print(ansi.info("No patterns found in the repository."))
            return 0

        data = [p.__dict__ for p in patterns]

        output = ""
        if args.format == "json":
            output = json.dumps(data, indent=2)
        elif args.format == "yaml":
            output = yaml.dump(data)
        elif args.format == "env":
            output = "\n".join([f"{p.name.upper()}={p.pattern}" for p in patterns])

        if args.output:
            try:
                with open(args.output, "w") as f:
                    f.write(output)
                print(ansi.success(f"Exported to {args.output}"))
            except Exception as e:
                print(ansi.error(f"Failed to export: {e}"))
                return 1
        else:
            print(output)

        return 0
