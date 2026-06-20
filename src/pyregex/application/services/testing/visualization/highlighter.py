from __future__ import annotations
from pyregex.application.services.testing.base import TestingState, MatchResult
from pyregex.utils import ansi


class TestingHighlighter:
    """Renders regex matches with ANSI colors and markers."""

    def format_match(self, result: MatchResult) -> str:
        """Formats a single match with its context and markers."""
        line = result.context or result.value
        start, end = result.span

        # Colorized Line
        # (Simplified: highlight only the first match occurrence in the context for this specific result)
        colored_line = (
            f"{line[:start]}{ansi.FG_GREEN}{line[start:end]}{ansi.RESET}{line[end:]}"
        )

        # Pointer Markers
        padding = " " * start
        markers = "^" * (end - start)
        pointer_line = f"{padding}{ansi.FG_CYAN}{markers}{ansi.RESET}"

        header = f"{ansi.FG_BLUE}[Line {result.line_number}]{ansi.RESET}"
        return f"{header} {colored_line}\n           {pointer_line}"

    def render_all(self, state: TestingState) -> str:
        """Renders the full state as a pretty string."""
        if not state.matches:
            return f"{ansi.FG_RED}No matches found.{ansi.RESET}"

        output = []
        output.append(f"{ansi.FG_CYAN}--- Testing Results ---{ansi.RESET}")
        output.append(f"Total Matches: {len(state.matches)}")
        output.append(f"Duration: {state.duration:.4f}s\n")

        for i, match in enumerate(state.matches[:10]):  # Limit to first 10 for preview
            output.append(f"[{i + 1}] {self.format_match(match)}")

        if len(state.matches) > 10:
            output.append(f"... and {len(state.matches) - 10} more matches.")

        return "\n".join(output)
