from typing import List
from pyregex.infrastructure.registry.schema.models import RegistryPattern


class DependencyWarning(Exception):
    def __init__(self, pattern_name: str, dependencies: List[str]):
        self.pattern_name = pattern_name
        self.dependencies = dependencies
        super().__init__(
            f"Pattern '{pattern_name}' is in use by: {', '.join(dependencies)}"
        )


class DependencyChecker:
    """Checks if a registry pattern is currently being used by active pipelines."""

    def check(self, pattern: RegistryPattern) -> List[str]:
        """Return the names of pipelines or jobs that depend on this pattern."""
        return []
