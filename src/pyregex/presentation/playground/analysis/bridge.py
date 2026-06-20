"""Playground — Analysis Bridge.

Connects the existing AdvancedExplainer to the playground for
real-time complexity, narrative, and warning analysis.
"""

from __future__ import annotations
from typing import Any, Optional
from pyregex.presentation.playground.core.state import ComplexityInfo, ExplanationInfo


class ExplainBridge:
    """
    Bridge between the Playground and the AdvancedExplainer engine.

    Lazy-loads the explainer and provides simplified analysis results
    suitable for real-time display.
    """

    def __init__(self):
        self._explainer = None
        self._cache: dict[str, dict] = {}
        self._max_cache = 100

    @property
    def explainer(self):
        if self._explainer is None:
            from pyregex.domain.explain.engine import AdvancedExplainer

            self._explainer = AdvancedExplainer()
        return self._explainer

    def analyze(self, pattern: str) -> dict[str, Any]:
        """Full analysis with caching."""
        if pattern in self._cache:
            return self._cache[pattern]

        result = self.explainer.explain(pattern)
        self._cache[pattern] = result
        if len(self._cache) > self._max_cache:
            oldest = next(iter(self._cache))
            del self._cache[oldest]

        return result

    def get_complexity(self, pattern: str) -> ComplexityInfo:
        """Get complexity info for a pattern."""
        if not pattern:
            return ComplexityInfo()

        result = self.analyze(pattern)
        if not result.get("success"):
            return ComplexityInfo()

        redos = result.get("redos", {})
        if redos and redos.get("complexity"):
            notation = redos["complexity"]
            cx_score = redos.get("complexity_score", 50)
            notation_to_level = {
                "O(N)": "low",
                "O(N²)": "high",
                "O(N³)": "critical",
                "O(2^N)": "critical",
            }
            level = notation_to_level.get(notation, "medium")
            backtrack = "none"
            if redos.get("is_vulnerable"):
                backtrack = "critical"
            elif notation != "O(N)":
                backtrack = "high"

            warns = result.get("warnings", [])
            sugs = result.get("suggestions", [])
            for v in redos.get("vulnerabilities", []):
                warns.append(f"ReDoS: {v.get('description', '')}")

            return ComplexityInfo(
                score=cx_score,
                level=level,
                backtrack_risk=backtrack,
                warnings=[str(w) for w in warns],
                suggestions=[str(s) for s in sugs],
            )

        # Fallback to legacy scoring
        raw_score = result.get("complexity", 0)
        try:
            score = int(raw_score) if not isinstance(raw_score, int) else raw_score
        except (ValueError, TypeError):
            score = 50

        warns = result.get("warnings", [])
        sugs = result.get("suggestions", [])

        if score <= 20:
            level = "low"
        elif score <= 50:
            level = "medium"
        elif score <= 80:
            level = "high"
        else:
            level = "critical"

        backtrack = "none"
        for w in warns:
            wl = w.lower() if isinstance(w, str) else ""
            if "backtrack" in wl or "catastrophic" in wl:
                backtrack = "critical"
            elif "nested" in wl and "quantifier" in wl:
                backtrack = "high" if backtrack == "none" else backtrack

        return ComplexityInfo(
            score=score,
            level=level,
            backtrack_risk=backtrack,
            warnings=[str(w) for w in warns],
            suggestions=[str(s) for s in sugs],
        )

    def get_redos_report(self, pattern: str) -> dict:
        """Get full ReDoS analysis report."""
        if not pattern:
            return {}
        result = self.analyze(pattern)
        return result.get("redos", {})

    def get_explanation(self, pattern: str) -> ExplanationInfo:
        """Get narrative explanation for a pattern."""
        if not pattern:
            return ExplanationInfo()

        result = self.analyze(pattern)
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            return ExplanationInfo(narrative=[f"Error: {error}"])

        return ExplanationInfo(
            narrative=result.get("narrative", []),
            tree=result.get("tree", ""),
            mermaid=result.get("mermaid", ""),
        )

    def get_narrative_text(self, pattern: str) -> list[str]:
        """Get just the narrative lines."""
        info = self.get_explanation(pattern)
        return info.narrative if info.narrative else ["(sin análisis disponible)"]

    def get_tree(self, pattern: str) -> str:
        """Get AST tree representation."""
        info = self.get_explanation(pattern)
        return info.tree

    def get_complexity_badge(self, pattern: str) -> str:
        """Get a visual badge for complexity: ●●●○○"""
        c = self.get_complexity(pattern)
        filled = min(5, c.score // 20)
        empty = 5 - filled
        colors = {0: "", 1: "", 2: "", 3: "", 4: "", 5: ""}
        return f"{'●' * filled}{'○' * empty} {colors.get(filled, '')} {c.level}"

    def invalidate_cache(self, pattern: Optional[str] = None) -> None:
        if pattern:
            self._cache.pop(pattern, None)
        else:
            self._cache.clear()
