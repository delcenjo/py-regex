from __future__ import annotations
import argparse
from pathlib import Path
from typing import TYPE_CHECKING, Any
from tqdm import tqdm

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi
from pyregex.application.services.validate.engine import ValidateEngine
from pyregex.application.services.validate import report as vreport

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class ValidateCommand(BaseCommand):
    """Validates data against regex patterns or JSON schemas."""

    @property
    def name(self) -> str:
        return "validate"

    @property
    def help(self) -> str:
        return "Validate data against regex or schema"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument("path", help="The path to validate")
        parser.add_argument("--type", help="The validation type (e.g. email, phone)")
        parser.add_argument("--schema", help="Path to JSON schema")
        parser.add_argument("--regex", help="Custom regex pattern")
        parser.add_argument(
            "--fail-fast", action="store_true", help="Fail on first error"
        )
        parser.add_argument(
            "--column", help="Column name/index for delimiter-based files"
        )
        parser.add_argument("--json", action="store_true", help="Output in JSON format")
        parser.add_argument("--summary", action="store_true", help="Show summary only")
        parser.add_argument(
            "--parallel", type=int, help="Number of workers (0 for auto)"
        )
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        engine = ValidateEngine()
        path = args.path

        if not Path(path).exists():
            print(ansi.error(f"Path not found: {path}"))
            return 1

        if Path(path).is_dir():
            max_workers = getattr(args, "parallel", None)
            print(ansi.info(f"Validating directory: {path}"))

            with tqdm(desc="Validating", unit="file") as pbar:
                success_count, total_count = engine.validate_directory(
                    str(path),
                    type_name=args.type,
                    fail_fast=args.fail_fast,
                    column=args.column,
                    max_workers=max_workers,
                    progress_callback=lambda: pbar.update(1),
                )

            if success_count == total_count:
                print(ansi.success(f"All {total_count} files are valid."))
            else:
                print(
                    ansi.error(
                        f"Validation failed for {total_count - success_count} files."
                    )
                )
            return 0 if success_count == total_count else 1

        try:
            if args.schema:
                if not Path(args.schema).exists():
                    print(ansi.error(f"Schema file not found: {args.schema}"))
                    return 1
                result = engine.validate_schema(args.schema, path)
            elif args.type:
                result = engine.validate_regex(
                    type_name=args.type,
                    path=path,
                    fail_fast=args.fail_fast,
                    column=args.column,
                    custom_regex=args.regex,
                )
            elif args.regex:
                result = engine.validate_regex(
                    type_name="custom",
                    path=path,
                    fail_fast=args.fail_fast,
                    column=args.column,
                    custom_regex=args.regex,
                )
            else:
                print(
                    ansi.error(
                        "Please specify a validation type (e.g., email, dni) or --schema / --regex."
                    )
                )
                return 1
        except Exception as e:
            print(ansi.error(str(e)))
            return 1

        if args.json:
            print(vreport.render_json(result))
        elif args.summary:
            print(vreport.render_summary(result))
        else:
            print(vreport.render_detailed_report(result))

        return 0 if result.invalid == 0 else 1
