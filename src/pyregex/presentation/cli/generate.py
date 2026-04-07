from __future__ import annotations
import argparse
import json
from typing import TYPE_CHECKING, Any

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi
from pyregex.application.services.generate_service import SyntheticEngine

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class GenerateCommand(BaseCommand):
    """Generates synthetic data from patterns."""

    @property
    def name(self) -> str:
        return "generate"

    @property
    def help(self) -> str:
        return "Generate synthetic data from patterns"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument(
            "type", help="The type of data to generate (e.g. email, phone)"
        )
        parser.add_argument(
            "--count", type=int, default=10, help="Number of items to generate"
        )
        parser.add_argument(
            "--format", default="list", help="Output format (list, json, csv)"
        )
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        engine = SyntheticEngine(registry=cli.registry)
        try:
            items = engine.generate(args.type, count=args.count)
            if args.format == "json":
                print(json.dumps(items, indent=2))
            elif args.format == "csv":
                print("\n".join(items))
            else:
                for i, item in enumerate(items, 1):
                    print(f"{i}. {item}")
            return 0
        except Exception as e:
            print(ansi.error(f"Generation failed: {e}"))
            return 1
