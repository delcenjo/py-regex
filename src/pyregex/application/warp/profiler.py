"""Warp Profiler — execution engine.

Orchestrates the running of fuzzed payloads while tracking precise hardware metrics.
"""

from __future__ import annotations
import re
import time
import threading
import gc
import psutil
import os

from pyregex.domain.warp.models import BenchProfile, IterationTick
from pyregex.domain.warp.fuzzer.pump_fuzzer import PumpFuzzer
from pyregex.application.warp.mathstat import MathProfiler


class TimeoutInterrupt(Exception):
    pass


def _regex_worker(pattern: str, text: str, result_box: list):
    try:
        compiled = re.compile(pattern)
        match = compiled.search(text)
        result_box.append(match is not None)
    except re.error as e:
        result_box.append(e)


class WarpEngine:
    """The dynamic profiler execution engine."""

    def __init__(self, timeout_seconds: float = 2.0):
        self.timeout_seconds = timeout_seconds
        self.fuzzer = PumpFuzzer()
        self.math_profiler = MathProfiler()
        self._process = psutil.Process(os.getpid())

    def profile(self, pattern: str) -> BenchProfile:
        """Execute a full profile run against a dynamically fuzzed pattern."""
        profile = BenchProfile(pattern=pattern)

        try:
            payloads = self.fuzzer.generate_payloads(pattern, stages=8, multiplier=1.5)
        except Exception:
            payloads = ["a" * int(10 * (1.5**i)) for i in range(8)]

        gc.disable()  # avoids GC pauses skewing timing

        try:
            for text in payloads:
                tick = self._run_tick(pattern, text)
                profile.ticks.append(tick)
                if tick.is_timeout:
                    profile.timeout_hit = True
                    break
        finally:
            gc.enable()

        if profile.ticks:
            profile.total_time_ms = sum(t.time_ms for t in profile.ticks)
            profile.max_memory_alloc_bytes = max(
                t.memory_alloc_bytes for t in profile.ticks
            )
            profile.max_cpu_percent = max(t.cpu_percent for t in profile.ticks)

            curve, r2 = self.math_profiler.analyze_complexity(profile.ticks)
            profile.base_complexity = curve
            profile.r_squared = r2

        return profile

    def _run_tick(self, pattern: str, text: str) -> IterationTick:
        """Runs the regex in a thread to enforce timeouts and tracks hardware metrics."""
        result_box = []
        worker = threading.Thread(
            target=_regex_worker, args=(pattern, text, result_box), daemon=True
        )

        start_time = time.perf_counter()
        start_mem = self._process.memory_info().rss
        self._process.cpu_percent(interval=None)  # Reset CPU tracker

        worker.start()
        worker.join(timeout=self.timeout_seconds)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        end_mem = self._process.memory_info().rss
        mem_alloc = max(0, end_mem - start_mem)
        cpu_pct = self._process.cpu_percent(interval=None)

        is_timeout = worker.is_alive()
        is_match = False

        if not is_timeout and result_box:
            res = result_box[0]
            if isinstance(res, Exception):
                pass
            else:
                is_match = res

        return IterationTick(
            input_length=len(text),
            time_ms=elapsed_ms,
            memory_alloc_bytes=mem_alloc,
            cpu_percent=cpu_pct,
            is_timeout=is_timeout,
            is_match=is_match,
        )
