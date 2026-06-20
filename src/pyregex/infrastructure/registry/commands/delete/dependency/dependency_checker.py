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
        """
        Checks for dependencies.
        In a full enterprise environment, this would scan workflow configs,
        audit jobs, or transform pipelines.
        For now, this is a mock implementation that represents the 'PRO' safety tier.
        """
        dependencies = []

        # Mocking a dependency check for the word 'critical'
        if "critical" in pattern.name.lower():
            dependencies.append("pipeline: logs_cleaning")
            dependencies.append("audit: pci_dss_scan")

        if dependencies:
            raise DependencyWarning(pattern.name, dependencies)

        return dependencies
