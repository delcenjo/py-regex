from __future__ import annotations
import argparse
import sys
import os
from typing import TYPE_CHECKING, Any
from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi, validators
from pyregex.i18n import translator as i18n

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class TestCommand(BaseCommand):
    """Executes a regex pattern test against text, files, stdin, or runs Sentinel test suites."""

    @property
    def name(self) -> str:
        return "test"

    @property
    def help(self) -> str:
        return "Run Sentinel Test Suites or quick regex string validation"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        # New Sentinel Arguments
        parser.add_argument(
            "path", nargs="?", help="Path to a test suite dir or .regex.yaml file"
        )
        parser.add_argument(
            "--coverage", action="store_true", help="Calculate AST branch coverage"
        )

        # Legacy Quick Test Arguments
        parser.add_argument(
            "-p", "--pattern", nargs="+", help="The regex pattern(s) to test"
        )
        parser.add_argument("-t", "--text", help="The text string to test against")
        parser.add_argument("-f", "--file", help="The file path to test against")
        parser.add_argument(
            "-i", "--ignore-case", action="store_true", help="Ignore case"
        )
        parser.add_argument(
            "-m", "--multiline", action="store_true", help="Multiline mode"
        )
        parser.add_argument("-s", "--dotall", action="store_true", help="Dotall mode")
        parser.add_argument(
            "-l", "--line-by-line", action="store_true", help="Line-by-line testing"
        )
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        # 1. Run Sentinel Test Suite Engine
        if args.path and os.path.exists(args.path):
            from pyregex.application.sentinel.discovery import TestDiscoverer
            from pyregex.application.sentinel.runner import TestSuiteRunner
            from pyregex.presentation.sentinel.reporter import SentinelReporter

            discoverer = TestDiscoverer()
            suites = discoverer.discover(args.path)

            if not suites:
                print(
                    f"{ansi.warning('Warn:')} No Sentinel Test Suites (*.regex.yaml) found in {args.path}"
                )
                return 1

            reporter = SentinelReporter()
            reporter.print_welcome()

            results = []
            for suite in suites:
                runner = TestSuiteRunner(suite)
                result = runner.run()
                results.append(result)
                reporter.report_suite(result)
                if args.coverage:
                    reporter.report_coverage(result)

            reporter.report_summary(results)
            return 0 if all(r.success for r in results) else 1

        # 2. Run Legacy Quick Command
        if not args.pattern:
            print(
                ansi.error(
                    i18n.t(
                        "common.error",
                        message="Pattern or Test Suite path is required.",
                    )
                )
            )
            return 1

        cli.history_repo.add(args.pattern[0], "test")
        flags = validators.parse_flags(args.ignore_case, args.multiline, args.dotall)

        text = args.text
        file_path = args.file
        stream = None

        if not text and not file_path:
            if not sys.stdin.isatty():
                stream = sys.stdin
            else:
                print(
                    ansi.error(
                        i18n.t(
                            "common.error",
                            message="Input text, file, or piped stream is required.",
                        )
                    )
                )
                return 1

        state = cli.testing_controller.run_tests(
            patterns_or_intents=args.pattern,
            text=text,
            file_path=file_path,
            stream=stream,
            flags=flags,
        )
        print(cli.testing_controller.highlighter.render_all(state))
        return 0 if state.matches else 1
