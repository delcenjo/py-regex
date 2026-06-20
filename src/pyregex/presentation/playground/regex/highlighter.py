"""Playground — Match Highlighter.

Generates highlighted text fragments for displaying matches in the input.
"""

from __future__ import annotations
from dataclasses import dataclass

from pyregex.presentation.playground.core.state import MatchInfo


@dataclass
class TextFragment:
    """A fragment of text with optional highlight info."""

    text: str
    start: int
    end: int
    is_match: bool = False
    match_index: int = -1  # which match (0-indexed)
    group_index: int = -1  # which group (-1 = full match)
    style: str = ""  # e.g. 'match', 'group_1', 'group_2', 'error'

    @property
    def length(self) -> int:
        return self.end - self.start


class MatchHighlighter:
    """
    Generates highlighted fragments for the input text.

    Takes match info and produces a list of TextFragments where
    matched regions are marked with styles.
    """

    # Default color rotation for match groups
    MATCH_STYLES = [
        "bg:#ff6b6b40",
        "bg:#ffd93d40",
        "bg:#6bcb7740",
        "bg:#4d96ff40",
        "bg:#ff922b40",
        "bg:#cc5de840",
        "bg:#20c99740",
        "bg:#748ffc40",
    ]
    GROUP_STYLES = [
        "fg:#ff6b6b bold",
        "fg:#ffd93d bold",
        "fg:#6bcb77 bold",
        "fg:#4d96ff bold",
        "fg:#ff922b bold",
        "fg:#cc5de8 bold",
        "fg:#20c997 bold",
        "fg:#748ffc bold",
    ]

    def highlight(
        self, text: str, matches: list[MatchInfo], show_groups: bool = True
    ) -> list[TextFragment]:
        """
        Generate highlighted fragments for the entire text.

        Matched regions get 'match' style, unmatched regions are plain.
        If show_groups, capture groups get individual group styles.
        """
        if not text:
            return []

        if not matches:
            return [TextFragment(text=text, start=0, end=len(text))]

        fragments: list[TextFragment] = []
        pos = 0

        for i, match in enumerate(matches):
            if match.start > pos:
                fragments.append(
                    TextFragment(
                        text=text[pos : match.start],
                        start=pos,
                        end=match.start,
                    )
                )

            style_idx = i % len(self.MATCH_STYLES)

            if show_groups and match.group_spans:
                # Break match into group sub-fragments
                match_pos = match.start
                for g_idx, (gs, ge) in enumerate(match.group_spans):
                    if gs > match_pos:
                        fragments.append(
                            TextFragment(
                                text=text[match_pos:gs],
                                start=match_pos,
                                end=gs,
                                is_match=True,
                                match_index=i,
                                style=self.MATCH_STYLES[style_idx],
                            )
                        )
                    group_style_idx = g_idx % len(self.GROUP_STYLES)
                    fragments.append(
                        TextFragment(
                            text=text[gs:ge],
                            start=gs,
                            end=ge,
                            is_match=True,
                            match_index=i,
                            group_index=g_idx + 1,
                            style=self.GROUP_STYLES[group_style_idx],
                        )
                    )
                    match_pos = ge

                if match_pos < match.end:
                    fragments.append(
                        TextFragment(
                            text=text[match_pos : match.end],
                            start=match_pos,
                            end=match.end,
                            is_match=True,
                            match_index=i,
                            style=self.MATCH_STYLES[style_idx],
                        )
                    )
            else:
                fragments.append(
                    TextFragment(
                        text=text[match.start : match.end],
                        start=match.start,
                        end=match.end,
                        is_match=True,
                        match_index=i,
                        style=self.MATCH_STYLES[style_idx],
                    )
                )

            pos = match.end

        if pos < len(text):
            fragments.append(
                TextFragment(
                    text=text[pos:],
                    start=pos,
                    end=len(text),
                )
            )

        return fragments

    def highlight_line(
        self, line: str, line_offset: int, matches: list[MatchInfo]
    ) -> list[TextFragment]:
        """Highlight a single line of text (for line-by-line rendering)."""
        line_end = line_offset + len(line)
        relevant = [m for m in matches if m.start < line_end and m.end > line_offset]

        # Adjust match positions to be relative to this line
        adjusted = []
        for m in relevant:
            adjusted.append(
                MatchInfo(
                    text=m.text,
                    start=max(0, m.start - line_offset),
                    end=min(len(line), m.end - line_offset),
                    groups=m.groups,
                    named_groups=m.named_groups,
                    group_spans=[
                        (max(0, s - line_offset), min(len(line), e - line_offset))
                        for s, e in m.group_spans
                        if s < line_end and e > line_offset
                    ],
                )
            )

        return self.highlight(line, adjusted, show_groups=True)

    def get_match_summary(self, matches: list[MatchInfo]) -> list[str]:
        """Generate a text summary of all matches."""
        lines = []
        for i, m in enumerate(matches):
            txt = m.text if len(m.text) <= 40 else m.text[:37] + "..."
            lines.append(f'  Match {i + 1}: "{txt}" (pos {m.start}-{m.end})')

            if m.groups:
                for g_idx, g_val in enumerate(m.groups):
                    if g_val is not None:
                        lines.append(f'    Group {g_idx + 1}: "{g_val}"')

            if m.named_groups:
                for name, val in m.named_groups.items():
                    lines.append(f'    <{name}>: "{val}"')

        return lines
