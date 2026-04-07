class PyRegexError(Exception):
    """Base exception for all PyRegex custom errors."""

    pass


class ExecutionTimeoutError(PyRegexError):
    """Raised when a regex operation exceeds the allowed time limit (ReDoS guard)."""

    pass


class PatternNotFoundError(PyRegexError):
    """Raised when a requested pattern is not found in the registry."""

    pass
