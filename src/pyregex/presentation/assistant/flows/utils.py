"""Utility flows for PyRegex Assistant, focusing on actions and specialized tools."""

from __future__ import annotations

import argparse
import re
from typing import Optional, Any, TYPE_CHECKING

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from pyregex.domain.builders.base import RegexBuilder
from pyregex.domain.builders.generic import GenericBuilder
from pyregex.infrastructure.persistence.pattern_repository import SavedPattern
from pyregex.utils import ansi
from pyregex.i18n import translator as i18n

if TYPE_CHECKING:
    from pyregex.presentation.cli.cli import PyRegexCLI


class UtilsFlows:
    """Specialized utility flows that don't fit into standard categories."""

    def __init__(self, cli: "PyRegexCLI"):
        self.cli = cli

    def handle_custom_flow(
        self, args: argparse.Namespace | None = None
    ) -> tuple[Optional[RegexBuilder], list[str]]:
        """Interactive flow for creating custom patterns."""
        tags = ["custom"]
        current_pattern = ""

        options = ["edit", "test", "save", "q"]

        while True:
            if not args or not getattr(args, "subtype", None):
                ansi.print_banner(i18n.t("custom_menu.title"))
                for opt in options:
                    print(f" [{opt}] {i18n.t(f'custom_menu.{opt}')}")

            if not current_pattern:
                current_pattern = prompt("Regex: ").strip()

            if not current_pattern:
                return None, tags

            print(f"\n{ansi.label('Current Pattern:')} {ansi.regex_display(current_pattern)}")

            choice = self.cli._get_arg_or_prompt(
                args, "custom_subtype", "Custom >", options + ["q"]
            )
            if choice == "q" or not choice:
                break

            if choice == "edit":
                current_pattern = prompt("New Regex: ", default=current_pattern).strip()
            elif choice == "test":
                test_text = prompt("Test string: ").strip()
                if test_text:
                    match = re.search(current_pattern, test_text)
                    if match:
                        print(ansi.success(f"Match found: {match.group(0)}"))
                    else:
                        print(ansi.error("No match found."))
            elif choice == "save":
                name = prompt("Pattern name: ").strip()
                if name:
                    self.cli.pattern_repo.save(
                        SavedPattern(
                            name=name,
                            pattern=current_pattern,
                            description="Custom pattern",
                            tags=tags,
                        )
                    )
                    print(ansi.success(f"Saved as {name}"))
                    return GenericBuilder({"id": name, "pattern": current_pattern}), tags

            if args and getattr(args, "subtype", None):
                break

        # Return a simple GenericBuilder for the custom pattern
        entry = {"id": "custom", "pattern": current_pattern, "name": "Custom"}
        return GenericBuilder(entry) if current_pattern else None, tags

    def handle_perf_flow(
        self, args: argparse.Namespace | None = None
    ) -> tuple[Optional[RegexBuilder], list[str]]:
        """Professional interactive flow for performance optimization."""
        perf_service = self.cli.perf_service
        tags = ["optimized"]

        options = [
            "analyze",
            "optimize",
            "benchmark",
            "safe",
            "simplify",
            "anchor",
            "save",
            "q",
        ]

        if not args or not getattr(args, "subtype", None):
            ansi.print_banner(i18n.t("perf_menu.title"))
            for opt in options:
                print(f" [{opt}] {i18n.t(f'perf_menu.{opt}')}")

        choice = self.cli._get_arg_or_prompt(
            args, "perf_subtype", "Perf >", options + ["q"]
        )
        if choice == "q" or not choice:
            return None, tags

        current_pattern = self.cli._get_arg_or_prompt(
            args, "pattern", "Enter regex to optimize: "
        ).strip()

        while True:
            if not args or not getattr(args, "subtype", None):
                if current_pattern:
                    print(
                        f"\n{ansi.label('Pattern:')} {ansi.regex_display(current_pattern)}"
                    )

            if choice == "analyze" and current_pattern:
                report = self.cli.perf_service.analyze_performance(current_pattern)
                print(f"\n{ansi.bold(i18n.t('perf_menu.analyze_options.title'))}")
                color = (
                    ansi.success
                    if report["level"] == "LOW"
                    else (ansi.warning if report["level"] == "MED" else ansi.error)
                )
                print(
                    f" - {i18n.t('perf_menu.results.risk_level', level=color(report['level']))}"
                )
                print(f" - {ansi.label('Complexity:')} {report['complexity_score']}")
                print(f" - {i18n.t('perf_menu.results.risks')}")
                for risk in report["risks"]:
                    print(f"   ⚠ {risk}")
                if report["suggestions"]:
                    print(f"\n {ansi.bold('Suggestions:')}")
                    for sugg in report["suggestions"]:
                        print(f"   💡 {sugg}")

            elif choice == "optimize" and current_pattern:
                level = (
                    self.cli._get_arg_or_prompt(
                        args,
                        "perf_level",
                        i18n.t("perf_menu.prompts.select_optimization"),
                    )
                    .strip()
                    .lower()
                )
                current_pattern = perf_service.auto_optimize(
                    current_pattern, level=level
                )
                print(ansi.success("Pattern optimized."))

            elif choice == "benchmark" and current_pattern:
                res = self.cli.perf_service.benchmark_smart(current_pattern)
                if "error" not in res:
                    print(
                        ansi.info(
                            f"Avg Time: {res['avg_time_ms']:.6f}ms (tested on {res['test_text_len']} chars)"
                        )
                    )
                else:
                    print(ansi.error(f"Benchmark failed: {res['error']}"))

            elif choice == "safe" and current_pattern:
                if self.cli.perf_service.detect_redos_deep(current_pattern)[
                    "is_vulnerable"
                ]:
                    print(ansi.error(i18n.t("perf_menu.results.redos_alert")))
                    current_pattern = re.sub(
                        r"(\([^)]+\)[*+?])[*+?]", r"\1", current_pattern
                    )
                    print(ansi.success(f"Suggested safe version: {current_pattern}"))
                else:
                    print(
                        ansi.success("Pattern seems safe from basic ReDoS heuristics.")
                    )

            elif choice == "simplify" and current_pattern:
                current_pattern = perf_service.auto_optimize(
                    current_pattern, level="aggressive"
                )
                print(ansi.success("Pattern simplified."))

            elif choice == "anchor" and current_pattern:
                if not current_pattern.startswith("^"):
                    current_pattern = "^" + current_pattern
                if not current_pattern.endswith("$"):
                    current_pattern = current_pattern + "$"
                print(ansi.success("Anchors added."))

            elif choice == "save" and current_pattern:
                name = self.cli._get_arg_or_prompt(
                    args, "name", "Enter name for this optimized pattern: "
                )
                if name:
                    self.cli.pattern_repo.save(
                        SavedPattern(
                            name=name,
                            pattern=current_pattern,
                            description="Optimized pattern",
                            tags=tags,
                        )
                    )
                    print(ansi.success(f"Saved as {name}"))
                    entry = {"id": name, "pattern": current_pattern}
                    return GenericBuilder(entry), tags

            if args and getattr(args, "subtype", None):
                break

            choice = prompt("> ", completer=WordCompleter(options)).strip().lower()
            if choice == "q" or not choice:
                break

        entry = {"id": "perf", "pattern": current_pattern}
        return GenericBuilder(entry) if current_pattern else None, tags
