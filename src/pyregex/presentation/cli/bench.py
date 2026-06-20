from __future__ import annotations
import argparse
import time
import re
from typing import TYPE_CHECKING, Any

from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class BenchCommand(BaseCommand):
    """Executes a performance benchmark or Warp Profiler dynamic fuzzing."""

    @property
    def name(self) -> str:
        return "bench"

    @property
    def help(self) -> str:
        return "Benchmark regex performance or generate Warp profile"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument(
            "-p", "--pattern", nargs="+", required=True, help="Patterns to benchmark"
        )
        parser.add_argument("-t", "--text", help="Text to benchmark against")
        parser.add_argument("-f", "--file", help="File to benchmark against")
        parser.add_argument(
            "-n", "--iterations", type=int, default=1000, help="Number of iterations"
        )
        parser.add_argument(
            "--fuzz-redos",
            action="store_true",
            help="Use dynamic ReDoS pump payloads (Warp Engine)",
        )
        parser.add_argument(
            "--export-html", help="Path to export the interactive HTML dossier"
        )
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        if args.fuzz_redos or args.export_html:
            from pyregex.application.warp.profiler import WarpEngine
            from pyregex.presentation.warp.reporter import WarpReporter

            reporter = WarpReporter()
            reporter.print_welcome()

            engine = WarpEngine(timeout_seconds=2.0)

            for pattern in args.pattern:
                profile = engine.profile(pattern)
                reporter.report_profile(profile)

                if args.export_html:
                    from pyregex.infrastructure.warp.exporters.html_exporter import (
                        HtmlExporter,
                    )

                    exporter = HtmlExporter()
                    exporter.export(profile, args.export_html)
                    print(ansi.success(f"Dossier exported: {args.export_html}"))
            return 0

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
        else:
            print(
                ansi.error(
                    "Either --text, --file or --fuzz-redos is required for benchmarking."
                )
            )
            return 1

        ansi.print_banner(f"Performance Benchmark ({args.iterations} iterations)")

        for pattern in args.pattern:
            try:
                compiled = re.compile(pattern)

                start = time.perf_counter()
                for _ in range(args.iterations):
                    compiled.findall(content)
                end = time.perf_counter()

                duration = end - start
                avg = duration / args.iterations

                print(f"{ansi.label('Pattern:')} {ansi.regex_display(pattern)}")
                print(f"  Total: {duration:.4f}s | Avg: {avg * 1000:.4f}ms")
            except re.error:
                print(ansi.error(f"Invalid regex: {pattern}"))

        return 0
