from __future__ import annotations
from typing import Optional, List
from pyregex.application.services.testing.base import TestingState
from pyregex.application.services.testing.engine.executor import RegexExecutor
from pyregex.application.services.testing.input.reader import (
    StringReader,
    FileReader,
    StreamReader,
)
from pyregex.application.services.testing.matcher.global_matcher import GlobalMatcher
from pyregex.application.services.testing.visualization.highlighter import (
    TestingHighlighter,
)
from pyregex.application.services.quick.controller.quick_controller import (
    QuickController,
)


class TestingController:
    """Orchestrates the testing pipeline."""

    def __init__(self, quick_controller: Optional[QuickController] = None):
        self.quick_controller = quick_controller
        self.highlighter = TestingHighlighter()

    def run_tests(
        self,
        patterns_or_intents: List[str],
        text: Optional[str] = None,
        file_path: Optional[str] = None,
        stream=None,
        flags: int = 0,
    ) -> TestingState:

        # 1. Resolve Intents to Patterns
        executors = []
        for pat in patterns_or_intents:
            resolved_pattern = pat
            if self.quick_controller is not None:
                # Try to map natural language intent to a pattern
                builder, tags = self.quick_controller.process_intent(pat)
                if builder:
                    resolved_pattern = builder.build_pattern()
            try:
                executors.append(RegexExecutor(resolved_pattern, flags))
            except ValueError:
                # Skip invalid patterns or record them
                pass

        if not executors:
            return TestingState()  # No valid patterns

        matcher = GlobalMatcher(executors)

        # 2. Setup Input
        if text:
            reader = StringReader(text)
        elif file_path:
            reader = FileReader(file_path)
        else:
            reader = StreamReader(stream)

        # 3. Execute
        state = matcher.match_stream(reader)

        return state
