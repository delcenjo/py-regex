"""Nebula Assistant Engine — Request/Response Pipeline."""

from __future__ import annotations
import time
from typing import Callable, Optional

from pyregex.presentation.assistant.core.types import (
    PipelineRequest,
    PipelineResponse,
    Middleware,
    EventType,
)
from pyregex.presentation.assistant.core.events import EventBus


class Pipeline:
    """
    Processes commands through a middleware chain.

    Middleware is executed in LIFO order (last registered runs first as wrapper),
    forming an onion-like execution model:

       Timing → Validation → Logging → Handler
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        self._middleware: list[Middleware] = []
        self._event_bus = event_bus

    def use(self, middleware: Middleware) -> "Pipeline":
        """Add middleware to the pipeline. Returns self for chaining."""
        self._middleware.append(middleware)
        return self

    def execute(
        self,
        request: PipelineRequest,
        handler: Callable[[PipelineRequest], PipelineResponse],
    ) -> PipelineResponse:
        """Execute a request through the middleware chain."""
        start = time.perf_counter()

        try:
            chain = handler
            for mw in reversed(self._middleware):
                chain = self._wrap(mw, chain)

            response = chain(request)
            response.execution_time_ms = (time.perf_counter() - start) * 1000

            if self._event_bus:
                self._event_bus.emit_simple(
                    EventType.COMMAND_EXECUTED,
                    source="pipeline",
                    command=request.command,
                    success=response.success,
                    time_ms=response.execution_time_ms,
                )

            return response

        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            if self._event_bus:
                self._event_bus.emit_simple(
                    EventType.ERROR_OCCURRED,
                    source="pipeline",
                    command=request.command,
                    error=str(e),
                )
            return PipelineResponse(
                success=False, error=str(e), execution_time_ms=elapsed
            )

    def _wrap(self, middleware: Middleware, next_handler: Callable) -> Callable:
        """Create a closure that wraps the next handler with middleware."""

        def wrapped(request: PipelineRequest) -> PipelineResponse:
            return middleware.process(request, next_handler)

        return wrapped
