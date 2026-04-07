"""Playground — Central Engine.

Orchestrates all playground components:
- Listens to state changes (regex_text, input_text, flags)
- Triggers compilation, matching, analysis
- Updates computed state (matches, complexity, perf)
- Emits events for the UI to react to
"""

from __future__ import annotations
from typing import Optional, Any
import re
import time

from pyregex.presentation.playground.core.state import (
    PlaygroundState,
    MatchInfo,
    ComplexityInfo,
    PerfInfo,
    ExplanationInfo,
    ReplaceInfo,
)
from pyregex.presentation.playground.core.events import EventBus, PlaygroundEvent
from pyregex.presentation.playground.core.config import PlaygroundConfig
from pyregex.presentation.playground.core.history import UndoManager


class PlaygroundEngine:
    """
    Central coordinator for the Playground.

    Wires together:
    - State management (reactive properties)
    - Regex processing (compile, match, groups)
    - Analysis (complexity, warnings, explanation)
    - Performance metrics
    - Undo/redo history
    - Event bus for UI updates
    """

    def __init__(self, config: Optional[PlaygroundConfig] = None):
        self.config = config or PlaygroundConfig()
        self.state = PlaygroundState()
        self.events = EventBus()
        self.undo_manager = UndoManager(max_history=self.config.max_history)

        # Analysis bridge (lazy loaded)
        self._explainer = None

        # Wire state observers
        self.state.subscribe("regex_text", self._on_regex_change)
        self.state.subscribe("input_text", self._on_input_change)
        self.state.subscribe("flags", self._on_flags_change)
        self.state.subscribe("replace_text", self._on_replace_change)

    # ── Public API ──────────────────────────────────────────────────

    def set_regex(self, text: str) -> None:
        """Set regex text (triggers full recomputation)."""
        self.state.regex_text = text

    def set_input(self, text: str) -> None:
        """Set input text (triggers re-matching)."""
        self.state.input_text = text

    def set_replace(self, text: str) -> None:
        """Set replacement text."""
        self.state.replace_text = text

    def toggle_flag(self, flag: int) -> None:
        """Toggle a regex flag."""
        self.state.toggle_flag(flag)
        self.events.emit(PlaygroundEvent.FLAG_TOGGLED, source="engine", flag=flag)

    def load_pattern(self, regex: str, input_text: str = "", flags: int = 0) -> None:
        """Load a complete pattern configuration."""
        self.events.mute()
        self.state.regex_text = regex
        self.state.input_text = input_text or self.state.input_text
        self.state.flags = flags
        self.events.unmute()
        # Trigger full recomputation
        self._full_recompute()

    def undo(self) -> bool:
        """Undo the last change."""
        snapshot = self.undo_manager.undo()
        if snapshot:
            self.undo_manager.begin_restore()
            self.state.restore(snapshot)
            self.undo_manager.end_restore()
            self._full_recompute()
            self.events.emit(PlaygroundEvent.UNDO, source="engine")
            return True
        return False

    def redo(self) -> bool:
        """Redo the last undone change."""
        snapshot = self.undo_manager.redo()
        if snapshot:
            self.undo_manager.begin_restore()
            self.state.restore(snapshot)
            self.undo_manager.end_restore()
            self._full_recompute()
            self.events.emit(PlaygroundEvent.REDO, source="engine")
            return True
        return False

    def clear(self) -> None:
        """Clear all state."""
        self.state.regex_text = ""
        self.state.input_text = ""
        self.state.replace_text = ""
        self.state.flags = 0

    # ── State change handlers ─────────────────────────────────────

    def _on_regex_change(self, prop: str, state: PlaygroundState) -> None:
        """Called when regex text changes."""
        self._save_snapshot()
        self._full_recompute()
        self.events.emit(
            PlaygroundEvent.REGEX_CHANGED, source="engine", regex=state.regex_text
        )

    def _on_input_change(self, prop: str, state: PlaygroundState) -> None:
        """Called when input text changes."""
        self._save_snapshot()
        self._run_matching()
        self._update_replace()
        self.events.emit(PlaygroundEvent.INPUT_CHANGED, source="engine")

    def _on_flags_change(self, prop: str, state: PlaygroundState) -> None:
        """Called when flags change."""
        self._save_snapshot()
        self._full_recompute()

    def _on_replace_change(self, prop: str, state: PlaygroundState) -> None:
        """Called when replacement text changes."""
        self._update_replace()
        self.events.emit(PlaygroundEvent.REPLACE_CHANGED, source="engine")

    # ── Internal processing pipeline ──────────────────────────────

    def _full_recompute(self) -> None:
        """Full recomputation: compile → match → analyze → explain."""
        self._compile_regex()
        if self.state.compiled:
            self._run_matching()
            self._run_analysis()
            self._run_explanation()
            self._update_replace()

    def _compile_regex(self) -> None:
        """Safely compile the regex pattern."""
        pattern = self.state.regex_text
        if not pattern:
            self.state.compiled = None
            self.state.compile_error = None
            self.state.matches = []
            self.state.perf = PerfInfo()
            self.state.complexity = ComplexityInfo()
            return

        start = time.perf_counter()
        try:
            compiled = re.compile(pattern, self.state.flags)
            compile_time = (time.perf_counter() - start) * 1_000_000  # μs
            self.state.compiled = compiled
            self.state.compile_error = None
            self.state.perf = PerfInfo(compile_time_us=compile_time)
            self.events.emit(PlaygroundEvent.REGEX_COMPILED, source="engine")
        except re.error as e:
            self.state.compiled = None
            self.state.compile_error = str(e)
            self.state.matches = []
            self.events.emit(PlaygroundEvent.REGEX_ERROR, source="engine", error=str(e))

    def _run_matching(self) -> None:
        """Run matching with timeout protection."""
        if not self.state.compiled or not self.state.input_text:
            self.state.matches = []
            return

        start = time.perf_counter()
        matches: list[MatchInfo] = []
        timed_out = False

        try:
            deadline = start + (self.config.match_timeout_ms / 1000.0)
            for m in self.state.compiled.finditer(self.state.input_text):
                if time.perf_counter() > deadline:
                    timed_out = True
                    self.events.emit(PlaygroundEvent.MATCH_TIMEOUT, source="engine")
                    break
                matches.append(MatchInfo.from_match(m))
                if len(matches) >= self.config.max_matches:
                    break
        except Exception:
            pass

        match_time = (time.perf_counter() - start) * 1_000_000

        self.state.matches = matches
        self.state.perf = PerfInfo(
            compile_time_us=self.state.perf.compile_time_us,
            match_time_us=match_time,
            total_time_us=self.state.perf.compile_time_us + match_time,
            match_count=len(matches),
            input_length=len(self.state.input_text),
            timed_out=timed_out,
        )

        if matches:
            self.events.emit(
                PlaygroundEvent.MATCH_COMPLETED, source="engine", count=len(matches)
            )
        else:
            self.events.emit(PlaygroundEvent.MATCH_NONE, source="engine")

    def _run_analysis(self) -> None:
        """Run complexity analysis via the explain engine."""
        pattern = self.state.regex_text
        if not pattern:
            return

        try:
            if self._explainer is None:
                from pyregex.domain.explain.engine import AdvancedExplainer

                self._explainer = AdvancedExplainer()

            result = self._explainer.explain(pattern)

            if result.get("success"):
                score = result.get("complexity", 0)
                warns = result.get("warnings", [])
                sugs = result.get("suggestions", [])

                # Determine level
                if score <= 20:
                    level = "low"
                elif score <= 50:
                    level = "medium"
                elif score <= 80:
                    level = "high"
                else:
                    level = "critical"

                # Check for ReDoS indicators
                backtrack = "none"
                for w in warns:
                    wl = w.lower()
                    if "backtrack" in wl or "catastrophic" in wl or "redos" in wl:
                        backtrack = "critical"
                        break
                    elif "nested" in wl and "quantifier" in wl:
                        backtrack = "high"

                self.state.complexity = ComplexityInfo(
                    score=score,
                    level=level,
                    backtrack_risk=backtrack,
                    warnings=warns,
                    suggestions=sugs,
                )
                self.events.emit(
                    PlaygroundEvent.COMPLEXITY_UPDATED,
                    source="engine",
                    score=score,
                    level=level,
                )

                if backtrack != "none":
                    self.events.emit(
                        PlaygroundEvent.REDOS_DETECTED, source="engine", risk=backtrack
                    )
        except Exception:
            pass

    def _run_explanation(self) -> None:
        """Generate inline explanation."""
        pattern = self.state.regex_text
        if not pattern or not self._explainer:
            return

        try:
            result = self._explainer.explain(pattern)
            if result.get("success"):
                self.state.explanation = ExplanationInfo(
                    narrative=result.get("narrative", []),
                    tree=result.get("tree", ""),
                    mermaid=result.get("mermaid", ""),
                )
                self.events.emit(PlaygroundEvent.EXPLANATION_UPDATED, source="engine")
        except Exception:
            pass

    def _update_replace(self) -> None:
        """Update substitution preview."""
        if not self.state.compiled or not self.state.replace_text:
            self.state.replace_info = ReplaceInfo()
            return

        try:
            result, count = self.state.compiled.subn(
                self.state.replace_text, self.state.input_text
            )
            self.state.replace_info = ReplaceInfo(
                replacement=self.state.replace_text,
                result=result,
                count=count,
            )
        except Exception as e:
            self.state.replace_info = ReplaceInfo(
                replacement=self.state.replace_text,
                result=f"Error: {e}",
                count=0,
            )

    def _save_snapshot(self) -> None:
        """Save current state for undo."""
        self.undo_manager.push(self.state.snapshot())

    # ── Stats ─────────────────────────────────────────────────────

    def get_stats(self) -> dict[str, Any]:
        return {
            **self.state.get_summary(),
            "undo_depth": self.undo_manager.depth,
            "can_undo": self.undo_manager.can_undo,
            "can_redo": self.undo_manager.can_redo,
            "event_count": len(self.events.log),
        }

    def shutdown(self) -> None:
        """Clean shutdown."""
        self.events.emit(PlaygroundEvent.APP_EXIT, source="engine")
        self.events.clear()
