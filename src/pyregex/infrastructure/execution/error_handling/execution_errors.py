from typing import List


class ExecutionError(Exception):
    """Base exception for all Execution Subsystem errors."""

    pass


class TargetNotFoundError(ExecutionError):
    def __init__(self, target_path: str):
        super().__init__(f"Execution Target not found: {target_path}")


class CorruptedFileError(ExecutionError):
    def __init__(self, target_path: str, reason: str):
        super().__init__(f"Cannot read target {target_path}: {reason}")


class EmptyMatchWarning(ExecutionError):
    def __init__(self, pattern_name: str, target: str):
        super().__init__(
            f"Pattern '{pattern_name}' yielded 0 results against '{target}'."
        )


class PatternExecutionResolutionError(ExecutionError):
    def __init__(self, target: str, suggestions: List[str]):
        self.suggestions = suggestions
        msg = f"Pattern '{target}' not found in registry."
        super().__init__(msg)
