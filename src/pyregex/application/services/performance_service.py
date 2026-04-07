"""Service for analyzing and optimizing regex performance."""

from __future__ import annotations
import re
import time
from typing import Dict, List, Any


class RegexPerformanceService:
    """Handles performance analysis, ReDoS detection, and auto-optimization."""

    def analyze_performance(self, pattern: str) -> Dict[str, Any]:
        """Analyze regex for complexity and risks."""
        risks = []
        level = "LOW"

        # 1. Advanced ReDoS Detection
        redos_results = self.detect_redos_deep(pattern)
        if redos_results["is_vulnerable"]:
            risks.extend(redos_results["risks"])
            level = "HIGH"

        # 2. Complexity Analysis
        complexity_score = self._calculate_complexity(pattern)
        if complexity_score > 50:
            risks.append(
                f"High complexity score ({complexity_score}): many branches or nested groups"
            )
            if level == "LOW":
                level = "MED"

        # 3. Anchoring Check
        if not (pattern.startswith("^") or pattern.endswith("$")):
            risks.append("Unanchored pattern: scanning large text will be O(N*M)")
            if level == "LOW":
                level = "MED"

        return {
            "level": level,
            "risks": risks,
            "complexity_score": complexity_score,
            "is_anchored": pattern.startswith("^") and pattern.endswith("$"),
            "suggestions": self._generate_suggestions(pattern, risks),
        }

    def detect_redos_deep(self, pattern: str) -> Dict[str, Any]:
        """Deep structural analysis for ReDoS (Catastrophic Backtracking)."""
        risks = []
        is_vulnerable = False

        # Nested quantifiers: (a+)+, (.*)*
        nested_match = re.search(r"(\([^\)]*[*+?{][^\)]*\))[*+?{]", pattern)
        if nested_match:
            risks.append(
                f"Nested quantifier detected: '{nested_match.group(0)}'. This often causes exponential backtracking."
            )
            is_vulnerable = True

        # Overlapping alternations with quantifiers: (a|ab)+
        overlap_match = re.search(r"\(([^|)]+)\|\1[^)]*\)[*+?{]", pattern)
        if overlap_match:
            risks.append(
                f"Overlapping alternation in quantified group: '{overlap_match.group(0)}'."
            )
            is_vulnerable = True

        # Star height (nested stars): a*b*c* is O(N), but (a*)* is exponential
        if pattern.count("*") + pattern.count("+") > 5 and "(" in pattern:
            risks.append("High quantifier density in groups: verify with benchmarks.")

        return {"is_vulnerable": is_vulnerable, "risks": risks}

    def auto_optimize(self, pattern: str, level: str = "safe") -> str:
        """Apply automated optimization rules."""
        optimized = pattern

        # 1. Simplify alternations to classes: (a|b|c) -> [abc]
        optimized = re.sub(
            r"\(([a-zA-Z0-9])(?:\|([a-zA-Z0-9]))+\)",
            lambda m: (
                f"[{''.join(m.groups() if m.groups()[0] else m.group(0).replace('|', '').strip('()'))}]"
            ),
            optimized,
        )

        # 2. Atomic group simulation (Possessive Quantifiers): a+ -> a++ (if supported, here we use non-capture as hint)
        # 3. Flatten nested non-capturing groups: (?:(?:a)) -> (?:a)
        optimized = re.sub(r"\(\?:\(\?:\s*(.*?)\s*\)\)", r"(?:\1)", optimized)

        # 4. Merge adjacent character classes: [a-d][e-z] -> wait, this is risky without parsing

        # 5. Remove redundant quantifiers
        optimized = re.sub(r"([*+?])\1+", r"\1", optimized)

        return optimized

    def benchmark_smart(self, pattern: str, iterations: int = 500) -> Dict[str, Any]:
        """Benchmark with synthetic 'near-miss' data to trigger worst-case performance."""
        # Find some literal or simple part to build a near-miss
        prefix = re.search(r"^[a-zA-Z0-9]+", pattern)
        near_miss_text = (prefix.group(0) if prefix else "abc") * 100 + "!!!"

        try:
            compiled = re.compile(pattern)
        except re.error as e:
            return {"error": str(e)}

        start = time.perf_counter()
        for _ in range(iterations):
            compiled.search(near_miss_text)
        end = time.perf_counter()

        avg_time = (end - start) / iterations
        return {
            "avg_time_ms": avg_time * 1000,
            "test_text_len": len(near_miss_text),
            "iterations": iterations,
        }

    def benchmark(self, pattern: str, text: str, iterations: int = 1000) -> float:
        """Measure average execution time over multiple iterations."""
        try:
            compiled = re.compile(pattern)
        except re.error:
            return -1.0

        start = time.perf_counter()
        for _ in range(iterations):
            compiled.search(text)
        end = time.perf_counter()

        return (end - start) / iterations

    def _calculate_complexity(self, pattern: str) -> int:
        """Calculate a numeric complexity score."""
        score = len(pattern) / 10
        score += pattern.count("|") * 5
        score += pattern.count("(") * 3
        score += (pattern.count("*") + pattern.count("+")) * 2
        return int(score)

    def _generate_suggestions(self, pattern: str, risks: List[str]) -> List[str]:
        suggestions = []
        if any("anchored" in r.lower() for r in risks):
            suggestions.append(
                "Add '^' to the start or '$' to the end to limit the search space."
            )
        if any("nested" in r.lower() for r in risks):
            suggestions.append("Flatten nested quantifiers. Instead of (a+)+, use a+.")
        if "(" in pattern and "?:" not in pattern:
            suggestions.append(
                "Use non-capturing groups (?:...) if you don't need to extract the data."
            )
        return suggestions
