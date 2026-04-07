from __future__ import annotations
from typing import Dict, List, Any
from pyregex.utils import ansi


class ExplainFormatter:
    """Formats EXPLAIN outputs into simple, detailed, or expert modes."""

    def format_output(
        self,
        mode: str,
        pattern: str,
        translation: str,
        tags: List[str],
        metrics: Dict[str, Any],
        warnings: List[str],
    ) -> str:
        lines = []

        lines.append(f"{ansi.bold('Regex:')} {ansi.regex_display(pattern)}\n")

        if tags:
            tag_str = ", ".join(ansi.FG_MAGENTA + tag + ansi.RESET for tag in tags)
            lines.append(f"{ansi.bold('Recognized Patterns:')} {tag_str}\n")

        if warnings:
            lines.append(f"{ansi.bold(ansi.FG_YELLOW + 'Warnings:' + ansi.RESET)}")
            for w in warnings:
                lines.append(f"  {ansi.FG_RED}{w}{ansi.RESET}")
            lines.append("")

        if mode == "simple":
            # Just show tags or a very brief summary
            lines.append(f"{ansi.bold('Breakdown:')}")
            lines.append(translation)

        elif mode == "detailed":
            lines.append(f"{ansi.bold('Detailed Breakdown:')}")
            lines.append(translation)

        elif mode == "expert":
            lines.append(f"{ansi.bold('Structural Metrics:')}")
            lines.append(f"  Node Count:  {metrics['node_count']}")
            lines.append(f"  Max Depth:   {metrics['max_depth']}")
            lines.append(f"  Complexity:  {metrics['complexity_score']}")
            lines.append(
                f"  Lookarounds: {'Yes' if metrics['has_lookarounds'] else 'No'}"
            )
            lines.append("")
            lines.append(f"{ansi.bold('AST Interpretation:')}")
            lines.append(translation)

        return "\n".join(lines)
