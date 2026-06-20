"""Warp Profiler — ReDoS Pump Fuzzer.

Generates mathematically scaling 'poison' payloads by iterating
the pump paths discovered by the ReDoS NFA simulator.
"""

from __future__ import annotations
from typing import List

from pyregex.domain.explain.redos import ReDoSAnalyzer


class PumpFuzzer:
    """Uses ReDoS analysis to construct exponentially scaling malicious inputs."""

    def __init__(self, analyzer: ReDoSAnalyzer | None = None):
        self.analyzer = analyzer or ReDoSAnalyzer()

    def generate_payloads(
        self, pattern: str, stages: int = 5, multiplier: int = 2
    ) -> List[str]:
        """
        Produce a list of strings of increasing length designed to trigger
        the worst-case backtracking limit mapped to the pattern's Big-O.

        If the pattern is safe, this just returns generic increasing strings.
        """
        report = self.analyzer.analyze(pattern)

        base = "a"
        pump = "a"
        suffix = "X"

        if report.is_vulnerable and report.evil_input:
            evil = report.evil_input
            if "X" in evil:
                parts = evil.split("X")
                pump = parts[0]
                suffix = "X"
            else:
                pump = evil
                suffix = "!"

        payloads = []
        current_len = 5

        for _ in range(stages):
            payloads.append((pump * current_len) + suffix)
            current_len = int(current_len * multiplier)

        return payloads
