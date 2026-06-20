"""Playground — Group Extractor & Visualizer.

Extracts and formats capture groups from matches for the groups panel.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from pyregex.presentation.playground.core.state import MatchInfo


@dataclass
class GroupDetail:
    """Detailed info about a single capture group."""

    number: int
    name: str | None
    text: str
    start: int
    end: int
    match_index: int  # which match this group belongs to
    is_named: bool = False

    @property
    def display_id(self) -> str:
        if self.name:
            return f"<{self.name}>"
        return f"#{self.number}"


@dataclass
class GroupTable:
    """Complete group extraction for all matches."""

    groups: list[GroupDetail] = field(default_factory=list)
    total_groups_per_match: int = 0
    named_group_count: int = 0
    match_count: int = 0

    @property
    def has_groups(self) -> bool:
        return len(self.groups) > 0


class GroupExtractor:
    """
    Extracts and organizes capture group information from matches.

    Provides multiple views:
    - Flat list of all groups
    - Grouped by match
    - Grouped by group number
    - Table format for display
    """

    def extract(self, matches: list[MatchInfo]) -> GroupTable:
        """Extract all group details from matches."""
        if not matches:
            return GroupTable()

        groups: list[GroupDetail] = []

        for match_idx, match in enumerate(matches):
            for g_idx, g_val in enumerate(match.groups):
                if g_val is None:
                    continue

                name = None
                for n, v in match.named_groups.items():
                    if v == g_val:
                        name = n
                        break

                start = end = 0
                if g_idx < len(match.group_spans):
                    start, end = match.group_spans[g_idx]

                groups.append(
                    GroupDetail(
                        number=g_idx + 1,
                        name=name,
                        text=g_val,
                        start=start,
                        end=end,
                        match_index=match_idx,
                        is_named=name is not None,
                    )
                )

        named_count = len({g.name for g in groups if g.name})

        return GroupTable(
            groups=groups,
            total_groups_per_match=max((len(m.groups) for m in matches), default=0),
            named_group_count=named_count,
            match_count=len(matches),
        )

    def by_match(self, table: GroupTable) -> dict[int, list[GroupDetail]]:
        """Organize groups by match index."""
        result: dict[int, list[GroupDetail]] = {}
        for g in table.groups:
            if g.match_index not in result:
                result[g.match_index] = []
            result[g.match_index].append(g)
        return result

    def by_group_number(self, table: GroupTable) -> dict[int, list[GroupDetail]]:
        """Organize groups by group number across matches."""
        result: dict[int, list[GroupDetail]] = {}
        for g in table.groups:
            if g.number not in result:
                result[g.number] = []
            result[g.number].append(g)
        return result

    def format_table(self, table: GroupTable, max_width: int = 60) -> list[str]:
        """Format groups as a readable table."""
        if not table.has_groups:
            return ["  (sin grupos de captura)"]

        lines: list[str] = []
        by_match = self.by_match(table)

        for match_idx, groups in sorted(by_match.items()):
            lines.append(f"  ╭─ Match {match_idx + 1} ─╮")
            for g in groups:
                txt = (
                    g.text
                    if len(g.text) <= max_width
                    else g.text[: max_width - 3] + "..."
                )
                label = g.display_id
                lines.append(f'  │ {label:>8s} → "{txt}"')
            lines.append(f"  ╰─{'─' * 20}─╯")

        return lines

    def format_compact(self, table: GroupTable) -> str:
        """One-line summary of groups."""
        if not table.has_groups:
            return "Sin grupos"
        parts = []
        for g in table.groups[:5]:
            parts.append(f'{g.display_id}="{g.text[:15]}"')
        suffix = f" +{len(table.groups) - 5}" if len(table.groups) > 5 else ""
        return ", ".join(parts) + suffix
