"""Playground — Reactive State Management.

Central state container with observer pattern — when regex/input/flags change,
all subscribed panels and processors are notified automatically.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from enum import Enum
import re


class PanelFocus(Enum):
    REGEX = "regex"
    INPUT = "input"
    MATCHES = "matches"
    GROUPS = "groups"
    EXPLAIN = "explain"
    STATS = "stats"
    DEBUG = "debug"
    REPLACE = "replace"
    CHEATSHEET = "cheatsheet"


@dataclass
class MatchInfo:
    """A single match result."""

    text: str
    start: int
    end: int
    groups: tuple
    named_groups: dict[str, str]
    group_spans: list[tuple[int, int]]

    @classmethod
    def from_match(cls, m: re.Match) -> MatchInfo:
        return cls(
            text=m.group(0),
            start=m.start(),
            end=m.end(),
            groups=m.groups(),
            named_groups={k: v for k, v in m.groupdict().items() if v is not None},
            group_spans=[
                (m.start(i), m.end(i))
                for i in range(1, len(m.groups()) + 1)
                if m.group(i) is not None
            ],
        )


@dataclass
class ComplexityInfo:
    """Regex complexity metrics."""

    score: int = 0  # 0-100
    level: str = "low"  # low, medium, high, critical
    backtrack_risk: str = "none"  # none, low, medium, high, critical
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)


@dataclass
class PerfInfo:
    """Performance metrics for the last match operation."""

    compile_time_us: float = 0.0  # microseconds
    match_time_us: float = 0.0
    total_time_us: float = 0.0
    match_count: int = 0
    input_length: int = 0
    timed_out: bool = False


@dataclass
class ExplanationInfo:
    """Inline explanation of the regex."""

    narrative: list[str] = field(default_factory=list)
    anatomy: list[tuple[str, str, str]] = field(
        default_factory=list
    )  # (part, color, label)
    tree: str = ""
    mermaid: str = ""


@dataclass
class ReplaceInfo:
    """Substitution preview."""

    replacement: str = ""
    result: str = ""
    count: int = 0


class PlaygroundState:
    """
    Reactive state container for the Playground.

    Changes to any property trigger observer notifications.
    Observers are keyed by property name for granular updates.
    """

    def __init__(self):
        # ── Editable state ──
        self._regex_text: str = ""
        self._input_text: str = "Enter test text here..."
        self._replace_text: str = ""
        self._flags: int = 0
        self._focus: PanelFocus = PanelFocus.REGEX

        # ── Computed state (updated by engine) ──
        self._compiled: Optional[re.Pattern] = None
        self._compile_error: Optional[str] = None
        self._matches: list[MatchInfo] = []
        self._complexity: ComplexityInfo = ComplexityInfo()
        self._perf: PerfInfo = PerfInfo()
        self._explanation: ExplanationInfo = ExplanationInfo()
        self._replace_info: ReplaceInfo = ReplaceInfo()
        self._debug_steps: list[str] = []

        # ── Observers ──
        self._observers: dict[str, list[Callable]] = {}

        # ── Panel visibility ──
        self._visible_panels: set[PanelFocus] = {
            PanelFocus.REGEX,
            PanelFocus.INPUT,
            PanelFocus.MATCHES,
            PanelFocus.STATS,
        }

        # ── Flags ──
        self._flag_labels = {
            re.IGNORECASE: ("i", "Case-insensitive"),
            re.MULTILINE: ("m", "Multi-line (^ $ match line boundaries)"),
            re.DOTALL: ("s", "Dot matches newline"),
            re.VERBOSE: ("x", "Verbose (comments & whitespace)"),
            re.ASCII: ("a", "ASCII-only matching"),
            re.UNICODE: ("u", "Unicode matching"),
        }

    # ── Property accessors with change notification ──

    @property
    def regex_text(self) -> str:
        return self._regex_text

    @regex_text.setter
    def regex_text(self, value: str):
        if value != self._regex_text:
            self._regex_text = value
            self._notify("regex_text")

    @property
    def input_text(self) -> str:
        return self._input_text

    @input_text.setter
    def input_text(self, value: str):
        if value != self._input_text:
            self._input_text = value
            self._notify("input_text")

    @property
    def replace_text(self) -> str:
        return self._replace_text

    @replace_text.setter
    def replace_text(self, value: str):
        if value != self._replace_text:
            self._replace_text = value
            self._notify("replace_text")

    @property
    def flags(self) -> int:
        return self._flags

    @flags.setter
    def flags(self, value: int):
        if value != self._flags:
            self._flags = value
            self._notify("flags")

    @property
    def focus(self) -> PanelFocus:
        return self._focus

    @focus.setter
    def focus(self, value: PanelFocus):
        if value != self._focus:
            self._focus = value
            self._notify("focus")

    @property
    def compiled(self) -> Optional[re.Pattern]:
        return self._compiled

    @compiled.setter
    def compiled(self, value: Optional[re.Pattern]):
        self._compiled = value
        self._notify("compiled")

    @property
    def compile_error(self) -> Optional[str]:
        return self._compile_error

    @compile_error.setter
    def compile_error(self, value: Optional[str]):
        self._compile_error = value
        self._notify("compile_error")

    @property
    def matches(self) -> list[MatchInfo]:
        return self._matches

    @matches.setter
    def matches(self, value: list[MatchInfo]):
        self._matches = value
        self._notify("matches")

    @property
    def complexity(self) -> ComplexityInfo:
        return self._complexity

    @complexity.setter
    def complexity(self, value: ComplexityInfo):
        self._complexity = value
        self._notify("complexity")

    @property
    def perf(self) -> PerfInfo:
        return self._perf

    @perf.setter
    def perf(self, value: PerfInfo):
        self._perf = value
        self._notify("perf")

    @property
    def explanation(self) -> ExplanationInfo:
        return self._explanation

    @explanation.setter
    def explanation(self, value: ExplanationInfo):
        self._explanation = value
        self._notify("explanation")

    @property
    def replace_info(self) -> ReplaceInfo:
        return self._replace_info

    @replace_info.setter
    def replace_info(self, value: ReplaceInfo):
        self._replace_info = value
        self._notify("replace_info")

    @property
    def debug_steps(self) -> list[str]:
        return self._debug_steps

    @debug_steps.setter
    def debug_steps(self, value: list[str]):
        self._debug_steps = value
        self._notify("debug_steps")

    @property
    def visible_panels(self) -> set[PanelFocus]:
        return self._visible_panels

    @property
    def flag_labels(self) -> dict:
        return self._flag_labels

    # ── Flag toggling ──

    def toggle_flag(self, flag: int) -> None:
        """Toggle a regex flag on/off."""
        self.flags = self._flags ^ flag

    def has_flag(self, flag: int) -> bool:
        return bool(self._flags & flag)

    def get_active_flag_string(self) -> str:
        """Returns string like '(?im)' for active flags."""
        chars = []
        for flag, (char, _) in self._flag_labels.items():
            if self.has_flag(flag):
                chars.append(char)
        return f"(?{''.join(chars)})" if chars else ""

    # ── Panel visibility ──

    def toggle_panel(self, panel: PanelFocus) -> None:
        if panel in self._visible_panels:
            self._visible_panels.discard(panel)
        else:
            self._visible_panels.add(panel)
        self._notify("visible_panels")

    def is_panel_visible(self, panel: PanelFocus) -> bool:
        return panel in self._visible_panels

    # ── Observer pattern ──

    def subscribe(self, property_name: str, callback: Callable) -> None:
        """Subscribe to changes on a specific property."""
        if property_name not in self._observers:
            self._observers[property_name] = []
        self._observers[property_name].append(callback)

    def subscribe_all(self, callback: Callable) -> None:
        """Subscribe to all property changes."""
        self.subscribe("*", callback)

    def unsubscribe(self, property_name: str, callback: Callable) -> None:
        if property_name in self._observers:
            self._observers[property_name] = [
                cb for cb in self._observers[property_name] if cb != callback
            ]

    def _notify(self, property_name: str) -> None:
        """Notify observers of a property change."""
        for cb in self._observers.get(property_name, []):
            try:
                cb(property_name, self)
            except Exception:
                pass
        for cb in self._observers.get("*", []):
            try:
                cb(property_name, self)
            except Exception:
                pass

    # ── Snapshot for undo/redo ──

    def snapshot(self) -> dict[str, Any]:
        return {
            "regex_text": self._regex_text,
            "input_text": self._input_text,
            "replace_text": self._replace_text,
            "flags": self._flags,
        }

    def restore(self, snap: dict[str, Any]) -> None:
        self._regex_text = snap.get("regex_text", "")
        self._input_text = snap.get("input_text", "")
        self._replace_text = snap.get("replace_text", "")
        self._flags = snap.get("flags", 0)
        self._notify("regex_text")
        self._notify("input_text")
        self._notify("flags")

    # ── Stats summary ──

    def get_summary(self) -> dict[str, Any]:
        return {
            "regex_length": len(self._regex_text),
            "input_length": len(self._input_text),
            "match_count": len(self._matches),
            "has_error": self._compile_error is not None,
            "flags_active": bin(self._flags).count("1"),
            "complexity": self._complexity.level,
            "perf_us": self._perf.total_time_us,
        }
