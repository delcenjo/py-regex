from typing import List
from pyregex.infrastructure.registry.schema.models import RegistryPattern


class Sorter:
    """Sorts patterns based on the requested strategy."""

    @staticmethod
    def sort(patterns: List[RegistryPattern], sort_by: str) -> List[RegistryPattern]:
        if sort_by == "created":
            # Patterns are appended in insertion order, so reversing approximates newest-first.
            # Replace with sort(key=lambda p: p.metadata.created_at, reverse=True) once that field exists.
            return list(reversed(patterns))

        elif sort_by == "usage":
            # Uses version as a proxy until real usage stats are available.
            return sorted(patterns, key=lambda p: p.metadata.version, reverse=True)

        else:
            return sorted(patterns, key=lambda p: p.name.lower())
