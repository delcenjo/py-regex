"""Pump Generator — NFA-guided evil input construction.

Generates worst-case inputs for vulnerable patterns by using the
pump paths identified by the NFA simulator.
"""

from __future__ import annotations
import re
import time
import threading
from dataclasses import dataclass
from typing import Optional

from pyregex.domain.explain.redos.nfa.simulator import PumpPath


@dataclass
class PumpTestResult:
    """Result of testing a pump string against a pattern."""

    timed_out: bool = False
    elapsed_ms: float = 0.0
    pump_length: int = 0
    risk_confirmed: bool = False


class PumpGenerator:
    """Generates and tests evil inputs based on NFA analysis.

    Unlike the old BacktrackDetector which used regex heuristics,
    this builds pump strings from actual NFA ambiguity analysis.
    """

    def __init__(self, timeout_ms: int = 2000):
        self.timeout_ms = timeout_ms

    def generate_evil(self, pump_path: PumpPath, base_len: int = 25) -> str:
        """Generate evil input from a pump path."""
        return pump_path.generate_evil(base_len)

    def generate_scaled_inputs(
        self, pump_path: PumpPath, sizes: list[int] | None = None
    ) -> list[str]:
        """Generate inputs of varying sizes for empirical complexity testing."""
        if sizes is None:
            sizes = [5, 10, 15, 20, 25]
        return [pump_path.generate_evil(n) for n in sizes]

    def test_pump(self, pattern: str, evil_input: str) -> PumpTestResult:
        """Test a regex against an evil input with timeout protection."""
        try:
            compiled = re.compile(pattern)
        except re.error:
            return PumpTestResult()

        result_holder = {"done": False, "elapsed_ms": 0.0}
        start = time.perf_counter()

        def _worker():
            try:
                compiled.search(evil_input)
            except Exception:
                pass
            result_holder["done"] = True
            result_holder["elapsed_ms"] = (time.perf_counter() - start) * 1000

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join(timeout=self.timeout_ms / 1000.0)

        if not result_holder["done"]:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return PumpTestResult(
                timed_out=True,
                elapsed_ms=elapsed_ms,
                pump_length=len(evil_input),
                risk_confirmed=True,
            )

        elapsed_ms = result_holder["elapsed_ms"]
        return PumpTestResult(
            timed_out=False,
            elapsed_ms=elapsed_ms,
            pump_length=len(evil_input),
            risk_confirmed=elapsed_ms > 100,  # >100ms is suspicious
        )

    def empirical_complexity(self, pattern: str, pump_path: PumpPath) -> Optional[str]:
        """Estimate complexity empirically by measuring times at different sizes.

        Returns "O(N)", "O(N²)", "O(2^N)" based on growth rate.
        """
        sizes = [8, 12, 16, 20]
        times: list[float] = []

        for size in sizes:
            evil = pump_path.generate_evil(size)
            result = self.test_pump(pattern, evil)

            if result.timed_out:
                return "O(2^N)"
            times.append(result.elapsed_ms)

        if len(times) < 3:
            return None

        # Check growth rate: exponential doubles at each step
        # Linear: ratio ≈ 1.5x, Quadratic: ratio ≈ 4x, Exponential: ratio >> 10x
        ratios = []
        for i in range(1, len(times)):
            if times[i - 1] > 0.01:  # avoid division by near-zero
                ratios.append(times[i] / times[i - 1])

        if not ratios:
            return "O(N)"

        avg_ratio = sum(ratios) / len(ratios)

        if avg_ratio > 8:
            return "O(2^N)"
        elif avg_ratio > 3:
            return "O(N²)"
        else:
            return "O(N)"
