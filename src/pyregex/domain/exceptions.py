class PyRegexError(Exception):
    """Base exception for all PyRegex custom errors."""
    pass

class ExecutionTimeoutError(PyRegexError):
    """Raised when a regex operation exceeds the allowed time limit (ReDoS guard)."""
    pass

class PatternNotFoundError(PyRegexError):
    """Raised when a requested pattern is not found in the registry."""
    pass

class PyRegexDomainError(PyRegexError):
    """Base exception for all domain-specific errors."""
    pass

class CatalogDiscoveryError(PyRegexDomainError):
    """Raised when catalog discovery fails."""
    pass

class CatalogEntryNotFoundError(PyRegexDomainError):
    """Raised when a requested catalog entry is not found."""
    pass

class CatalogParseError(PyRegexDomainError):
    """Raised when a catalog YAML entry cannot be parsed."""
    pass

class RegexParseError(PyRegexDomainError):
    """Raised when regex parsing fails."""
    pass

class NFAConstructionError(PyRegexDomainError):
    """Raised when NFA construction fails."""
    pass

class ReDoSAnalysisError(PyRegexDomainError):
    """Raised when ReDoS analysis fails or is incomplete."""
    pass

class PatternValidationError(PyRegexDomainError):
    """Raised when pattern validation fails."""
    pass

class PatternPersistenceError(PyRegexDomainError):
    """Raised when writing or reading from pattern repository fails."""
    pass
