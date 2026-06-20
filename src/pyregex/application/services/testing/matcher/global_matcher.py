from __future__ import annotations
import time
from typing import List
from pyregex.application.services.testing.base import TestingState
from pyregex.application.services.testing.engine.executor import RegexExecutor
from pyregex.application.services.testing.input.reader import InputReader


class GlobalMatcher:
    """Matches a regex against a stream of input lines."""

    def __init__(self, executors: List[RegexExecutor]):
        self.executors = executors

    def match_stream(self, reader: InputReader) -> TestingState:
        state = TestingState(start_time=time.time())
        line_num = 1

        try:
            for line in reader.read_lines():
                state.total_lines += 1
                state.total_bytes += len(line)

                for executor in self.executors:
                    matches = executor.execute_on_line(line, line_num)
                    state.matches.extend(matches)

                line_num += 1
        except Exception as e:
            state.errors.append(str(e))

        state.end_time = time.time()
        return state
