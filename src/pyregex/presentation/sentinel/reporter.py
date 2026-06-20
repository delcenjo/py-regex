"""Sentinel Engine — Terminal UI Reporter.

Displays test execution results in a beautiful, pytest/jest-like format
using the 'rich' console.
"""

from __future__ import annotations
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from pyregex.domain.sentinel.models import SuiteResult, TestStatus


class SentinelReporter:
    """Rich-based UI for Sentinel Test Suite Execution."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def print_welcome(self):
        """Prints the Sentinel startup banner."""
        self.console.print(
            "[bold bright_blue]Sentinel[/bold bright_blue] [dim]— PyRegex Mass Unit Testing Engine[/dim]"
        )
        self.console.print("=" * 60)

    def report_suite(self, result: SuiteResult):
        """Prints the detailed results of a single TestSuite."""
        # Header
        if result.success:
            panel_style = "green"
            status_text = "[bold green]PASS[/bold green]"
        else:
            panel_style = "red"
            status_text = "[bold red]FAIL[/bold red]"

        title = (
            f"{status_text} {result.suite_name} [dim]({result.total_tests} tests)[/dim]"
        )

        # Details Table for Failures
        if not result.success:
            self.console.print(f"\n[bold]{title}[/bold]")
            fail_table = Table(box=box.MINIMAL, expand=True, show_header=True)
            fail_table.add_column("Status", justify="center", width=8)
            fail_table.add_column("Input Text", style="cyan")
            fail_table.add_column("Assertion", style="yellow")
            fail_table.add_column("Reason", style="red")

            for t in result.results:
                if not t.passed:
                    status_lbl = (
                        "[red]FAIL[/red]"
                        if t.status == TestStatus.FAIL
                        else "[yellow]ERROR[/yellow]"
                    )
                    fake_mark = (
                        "[dim magenta](synthetic)[/dim magenta] "
                        if t.case.is_synthetic
                        else ""
                    )

                    input_trunc = t.case.input_text
                    if len(input_trunc) > 40:
                        input_trunc = input_trunc[:37] + "..."

                    assertion = (
                        "should_match=True"
                        if t.case.should_match
                        else "should_match=False"
                    )
                    reason = t.error_message or "Unknown failure"

                    fail_table.add_row(
                        status_lbl, f"{fake_mark}{input_trunc}", assertion, reason
                    )

            self.console.print(fail_table)
        else:
            self.console.print(
                f"{title}  [dim]{result.total_execution_time_ms:.1f}ms[/dim]"
            )

    def report_coverage(self, result: SuiteResult):
        """Prints AST Code Coverage analysis."""
        cov = result.coverage
        # Only show coverage if we parsed AST correctly
        if cov.total_branches == 0 and cov.total_quantifiers == 0:
            return

        self.console.print("\n[bold]AST Coverage Analysis[/bold]")

        cov_table = Table(box=box.SIMPLE, show_header=True)
        cov_table.add_column("Metric")
        cov_table.add_column("Score", justify="right")
        cov_table.add_column("Missed Nodes", style="dim red")

        # Format percentages safely
        b_pct = cov.branch_coverage_percent
        q_pct = cov.quantifier_coverage_percent

        def pct_color(val):
            if val == 100:
                return "green"
            if val > 80:
                return "yellow"
            return "red"

        b_str = f"[{pct_color(b_pct)}]{b_pct:.1f}%[/]"
        q_str = f"[{pct_color(q_pct)}]{q_pct:.1f}%[/]"

        missed_b_str = ", ".join(cov.missed_alternations[:3])
        if len(cov.missed_alternations) > 3:
            missed_b_str += f" ...and {len(cov.missed_alternations) - 3} more"

        missed_q_str = ", ".join(cov.missed_quantifiers[:3])
        if len(cov.missed_quantifiers) > 3:
            missed_q_str += f" ...and {len(cov.missed_quantifiers) - 3} more"

        cov_table.add_row(
            "Alternation Branches (|)",
            f"{cov.covered_branches}/{cov.total_branches} ({b_str})",
            missed_b_str or "-",
        )
        cov_table.add_row(
            "Quantifiers (*, +, ?)",
            f"{cov.covered_quantifiers}/{cov.total_quantifiers} ({q_str})",
            missed_q_str or "-",
        )

        self.console.print(cov_table)

    def report_summary(self, results: List[SuiteResult]):
        """Prints the final summary after all suites have run."""
        self.console.print("\n[bold]Test Suites Summary[/bold]")

        total_suites = len(results)
        passed_suites = sum(1 for r in results if r.success)
        failed_suites = total_suites - passed_suites

        total_tests = sum(r.total_tests for r in results)
        passed_tests = sum(r.passed_tests for r in results)
        failed_tests = sum(r.failed_tests for r in results)

        total_time = sum(r.total_execution_time_ms for r in results)

        t1 = Text("Suites: ")
        if failed_suites > 0:
            t1.append(f"{failed_suites} failed", style="bold red")
            t1.append(", ")
        t1.append(f"{passed_suites} passed", style="bold green")
        t1.append(f", {total_suites} total", style="dim")

        t2 = Text("Tests:  ")
        if failed_tests > 0:
            t2.append(f"{failed_tests} failed", style="bold red")
            t2.append(", ")
        t2.append(f"{passed_tests} passed", style="bold green")
        t2.append(f", {total_tests} total", style="dim")

        t3 = Text(f"Time:   {total_time / 1000.0:.2f}s", style="dim")

        panel = Panel(
            Text.assemble(t1, "\n", t2, "\n", t3),
            title="Sentinel Final Outcome",
            border_style="red" if failed_suites > 0 else "green",
        )
        self.console.print(panel)
        self.console.print()
