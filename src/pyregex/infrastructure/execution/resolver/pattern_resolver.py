from pyregex.infrastructure.registry.schema.models import RegistryPattern
from pyregex.application.services.registry_controller import RegistryController
from pyregex.infrastructure.execution.error_handling.execution_errors import (
    PatternExecutionResolutionError,
)
import difflib


class ExecutionResolver:
    """Finds the pattern for execution, bridging to the Registry."""

    def __init__(self, registry: RegistryController):
        self.registry = registry

    def resolve(self, pattern_name: str) -> RegistryPattern:
        """
        Attempts to resolve a pattern name.
        If it finds it, returns the full RegistryPattern.
        If not, raises PatternExecutionResolutionError with fuzzy suggestions.
        """
        all_patterns = self.registry.get_all()

        exact = next(
            (p for p in all_patterns if p.name.lower() == pattern_name.lower()), None
        )
        if exact:
            return exact

        suggestions = [
            p
            for p in all_patterns
            if pattern_name.lower() in p.name.lower()
            and p.name.lower() != pattern_name.lower()
        ]

        if not suggestions:
            names = [p.name for p in all_patterns]
            close_names = difflib.get_close_matches(
                pattern_name.lower(), [n.lower() for n in names], n=3, cutoff=0.4
            )
            for close_name in close_names:
                for p in all_patterns:
                    if p.name.lower() == close_name:
                        if p not in suggestions:
                            suggestions.append(p)
                        break

        raise PatternExecutionResolutionError(
            pattern_name, [s.name for s in suggestions[:3]]
        )
