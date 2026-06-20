"""Nebula Assistant Engine — Pipeline Middleware."""

from __future__ import annotations
import time
import logging
from typing import Callable
from datetime import datetime

from pyregex.presentation.assistant.core.types import PipelineRequest, PipelineResponse


logger = logging.getLogger("pyregex.assistant")


class ValidationMiddleware:
    """Sanitizes and validates incoming requests."""

    def process(
        self, request: PipelineRequest, next_handler: Callable
    ) -> PipelineResponse:
        request.command = request.command.strip()

        if not request.command:
            return PipelineResponse(success=False, error="Empty command")

        request.args = [a.strip() for a in request.args if a.strip()]

        return next_handler(request)


class LoggingMiddleware:
    """Logs all commands and their results for audit trail."""

    def __init__(self):
        self._log: list[dict] = []

    def process(
        self, request: PipelineRequest, next_handler: Callable
    ) -> PipelineResponse:
        entry = {
            "command": request.command,
            "args": request.args,
            "timestamp": datetime.now().isoformat(),
        }

        response = next_handler(request)

        entry["success"] = response.success
        entry["error"] = response.error
        entry["time_ms"] = response.execution_time_ms
        self._log.append(entry)

        logger.debug(
            f"[assistant] {request.command} → {'OK' if response.success else 'FAIL'} ({response.execution_time_ms:.1f}ms)"
        )

        return response

    @property
    def log(self) -> list[dict]:
        return list(self._log)


class TimingMiddleware:
    """Tracks execution time per command and provides statistics."""

    def __init__(self):
        self._timings: dict[str, list[float]] = {}

    def process(
        self, request: PipelineRequest, next_handler: Callable
    ) -> PipelineResponse:
        start = time.perf_counter()
        response = next_handler(request)
        elapsed = (time.perf_counter() - start) * 1000

        cmd = request.command
        if cmd not in self._timings:
            self._timings[cmd] = []
        self._timings[cmd].append(elapsed)

        return response

    def get_stats(self, command: str = "") -> dict:
        """Get timing statistics."""
        if command and command in self._timings:
            timings = self._timings[command]
            return {
                "command": command,
                "calls": len(timings),
                "avg_ms": sum(timings) / len(timings),
                "min_ms": min(timings),
                "max_ms": max(timings),
            }

        return {
            cmd: {
                "calls": len(t),
                "avg_ms": sum(t) / len(t),
            }
            for cmd, t in self._timings.items()
        }


class ErrorHandlerMiddleware:
    """Catches exceptions and converts them to PipelineResponse errors."""

    def process(
        self, request: PipelineRequest, next_handler: Callable
    ) -> PipelineResponse:
        try:
            return next_handler(request)
        except KeyboardInterrupt:
            return PipelineResponse(success=False, error="Interrupted by user")
        except Exception as e:
            logger.error(f"[assistant] Error in {request.command}: {e}")
            return PipelineResponse(
                success=False,
                error=f"{type(e).__name__}: {e}",
                warnings=[f"Command '{request.command}' failed unexpectedly"],
            )
