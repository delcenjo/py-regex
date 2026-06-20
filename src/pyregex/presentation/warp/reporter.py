"""Warp Profiler — Terminal Reporter UI.

Draws live benchmarking traces and mathematical summaries
into the terminal using the rich console.
"""

from __future__ import annotations
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from pyregex.domain.warp.models import BenchProfile, ComplexityCurve


class WarpReporter:
    """Renders Warp profiles on the local terminal."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def print_welcome(self):
        self.console.print(
            "\n[bold magenta]🚀 Warp Profiler[/bold magenta] [dim]— Empirical Complexity Benchmark[/dim]"
        )
        self.console.print("=" * 60)

    def report_profile(self, profile: BenchProfile):
        """Prints the profile ticks in a table and then the final summary."""
        # 1. Ticks table
        table = Table(show_header=True, header_style="bold cyan", expand=True)
        table.add_column("Iteration", justify="right", width=10)
        table.add_column("Payload Length", justify="right")
        table.add_column("CPU Time (ms)", justify="right")
        table.add_column("Mem Alloc (KB)", justify="right")
        table.add_column("Timeout", justify="center")

        for i, tick in enumerate(profile.ticks):
            time_str = f"{tick.time_ms:.3f}"
            if tick.time_ms > 100:
                time_str = f"[red]{time_str}[/red]"
            elif tick.time_ms > 20:
                time_str = f"[yellow]{time_str}[/yellow]"

            mem_str = f"{tick.memory_alloc_bytes / 1024.0:.1f}"
            t_out = "[bold red]YES[/bold red]" if tick.is_timeout else "[dim]no[/dim]"

            table.add_row(str(i + 1), str(tick.input_length), time_str, mem_str, t_out)

        self.console.print(table)
        self.console.print()

        # 2. Final Math Summary Panel
        is_danger = profile.base_complexity in (
            ComplexityCurve.QUADRATIC,
            ComplexityCurve.CUBIC,
            ComplexityCurve.EXPONENTIAL,
        )
        style = "red" if is_danger else "green"

        t1 = Text(
            f"Empirical Complexity: {profile.base_complexity.value}\n",
            style=f"bold {style}",
        )
        t2 = Text(f"Statistical R² Fit:   {profile.r_squared:.4f}\n", style="dim")

        t3 = Text.assemble(
            "\nMax CPU: ",
            (
                f"{profile.max_time_ms:.2f}ms"
                if hasattr(profile, "max_time_ms")
                else f"{max(t.time_ms for t in profile.ticks) if profile.ticks else 0:.2f}ms",
                "bold yellow",
            ),
        )
        t4 = Text.assemble(
            "\nMax Mem: ",
            (f"{profile.max_memory_alloc_bytes / 1024.0:.2f}KB", "bold cyan"),
        )

        t5 = Text()
        if profile.timeout_hit:
            t5 = Text(
                "\n\n⚠️ ENGINE BLOCKED: Timeout reached due to catastrophic backtracking.",
                style="bold red",
            )

        panel = Panel(
            Text.assemble(t1, t2, t3, t4, t5),
            title=f"Target: {profile.pattern}",
            border_style=style,
        )
        self.console.print(panel)
