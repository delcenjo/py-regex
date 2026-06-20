from __future__ import annotations
import argparse
from typing import TYPE_CHECKING, Any
from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi
from pyregex.i18n import translator as i18n
from pyregex.infrastructure.execution.error_handling.execution_errors import (
    ExecutionError,
    PatternExecutionResolutionError,
)

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class RunCommand(BaseCommand):
    """Executes a saved pattern against a target (text, file, or directory)."""

    @property
    def name(self) -> str:
        return "run"

    @property
    def help(self) -> str:
        return "Execute a saved pattern against a target"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument("name", help="Name of the saved pattern to run")
        parser.add_argument("-t", "--text", help="Text string to run against")
        parser.add_argument("-f", "--file", help="File or Directory target path")
        parser.add_argument(
            "--format",
            default="ansi",
            choices=["ansi", "json", "csv"],
            help="Output formatting",
        )
        parser.add_argument(
            "--global",
            dest="apply_global",
            action="store_true",
            help="Find all matches (global iter)",
        )
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        target_name = args.name
        text = args.text
        file_path = args.file
        output_format = args.format
        apply_global = getattr(args, "apply_global", False)

        target_input = text
        is_file = False

        if file_path:
            target_input = file_path
            is_file = True
        elif not text:
            # Fallback to stdin if not a TTY
            import sys

            if not sys.stdin.isatty():
                target_input = sys.stdin.read()
            else:
                print(
                    ansi.error(
                        i18n.t(
                            "common.error",
                            message="No input provided (use -t, -f, or pipe).",
                        )
                    )
                )
                return 1

        try:
            results = cli.execution_system.execute(
                pattern_name=target_name,
                target=target_input,
                is_file=is_file,
                output_format=output_format,
                apply_global=apply_global,
            )

            if output_format == "ansi":
                print(results)
            else:
                print(results)

            return 0

        except PatternExecutionResolutionError:
            print(ansi.error(f"Pattern '{target_name}' not found."))
            return 1
        except ExecutionError as e:
            print(ansi.error(f"Execution failed: {str(e)}"))
            return 1
        except Exception as e:
            print(ansi.error(f"An unexpected error occurred: {str(e)}"))
            return 1
