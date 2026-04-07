from __future__ import annotations
import argparse
from typing import TYPE_CHECKING, Any

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi
from pyregex.application.services.inference_engine import InferenceEngine

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class LearnCommand(BaseCommand):
    """Infers patterns from examples."""

    @property
    def name(self) -> str:
        return "learn"

    @property
    def help(self) -> str:
        return "Infer patterns from examples"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument("examples", nargs="*", help="Examples to learn from")
        parser.add_argument("--file", help="File with examples (one per line)")
        parser.add_argument(
            "--strict", action="store_true", help="Strict learning mode"
        )
        parser.add_argument("--save", help="Save the learned pattern with this name")
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        examples = []
        if args.examples:
            examples.extend(args.examples)
        if args.file:
            try:
                with open(args.file, "r") as f:
                    examples.extend([line.strip() for line in f if line.strip()])
            except Exception as e:
                print(ansi.error(f"Failed to read file: {e}"))
                return 1

        if not examples:
            print(ansi.error("No examples provided to learn from."))
            return 1

        engine = InferenceEngine()
        try:
            result = engine.learn(examples, strict=args.strict)
            pattern = result["pattern"]
            conf = result["confidence"]

            print(f"{ansi.label('Inferred Pattern:')} {ansi.regex_display(pattern)}")
            print(f"{ansi.label('Confidence Score:')} {int(conf * 100)}%")

            if args.save:
                cli.context.add_custom_pattern(args.save, pattern)
                cli.context.save()
                print(ansi.success(f"Pattern saved as '{args.save}' in .pyregex.yaml"))

            return 0
        except Exception as e:
            print(ansi.error(f"Inference failed: {e}"))
            return 1
