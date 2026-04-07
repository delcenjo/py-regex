"""Terminal highlighter for regex matches."""

from __future__ import annotations

from pyregex.utils import ansi
from pyregex.testing.tester import MatchResult


class Highlighter:
    """Highlights matches in text using ANSI colors."""

    def highlight_matches(self, text: str, matches: list[MatchResult]) -> str:
        """Render text with matches highlighted. Multiple patterns get different colors."""
        if not matches:
            return text

        # Sort matches by start position descending to replace from end
        # Also sort by length descending to handle nested matches (take longest)
        sorted_matches = sorted(
            matches, key=lambda m: (m.start, -(m.end - m.start)), reverse=True
        )

        result = text
        last_start = len(text) + 1

        for m in sorted_matches:
            # Avoid overlapping: if this match ends after the last match's start, skip it
            if m.end > last_start:
                continue

            if m.start < 0 or m.end > len(text):
                continue

            # Use original text to slice, then reconstruct
            # Since we iterate backwards, we don't need to worry about index shifts in 'text'
            match_text = text[m.start : m.end]
            highlighted = ansi.highlight(match_text, color_index=m.pattern_index)

            # We must be careful while replacing: we are working backwards on 'result'
            # but using 'text' as reference for content.
            # Actually, working on 'result' is fine if we only touch the parts before 'last_start'
            result = result[: m.start] + highlighted + result[m.end :]
            last_start = m.start

        return result

    def print_line_results(
        self, line_no: int, content: str, matches: list[MatchResult]
    ) -> None:
        """Print a single line result with match count and highlighting."""
        count = len(matches)
        count_str = ansi.bold(f"[{count}]").ljust(5)
        line_no_str = ansi.dim(f"{line_no}:").ljust(6)
        highlighted = self.highlight_matches(content, matches)
        print(f"{line_no_str} {count_str} {highlighted}")

    def print_file_matches(
        self, patterns: list[str], content: str, matches: list[MatchResult]
    ) -> None:
        """Print matches for an entire file with headers."""
        patterns_str = ", ".join([ansi.regex_display(p) for p in patterns])
        print(ansi.header(f"Results for patterns: {patterns_str}"))
        print(ansi.muted("-" * 40))

        highlighted = self.highlight_matches(content, matches)
        print(highlighted)
