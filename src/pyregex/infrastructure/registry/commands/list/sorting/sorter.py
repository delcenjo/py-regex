from typing import List
from pyregex.infrastructure.registry.schema.models import RegistryPattern


class Sorter:
    """Sorts patterns based on the requested strategy."""

    @staticmethod
    def sort(patterns: List[RegistryPattern], sort_by: str) -> List[RegistryPattern]:
        if sort_by == "created":
            # Reverse chronological (newest first)
            # Metadata currently doesn't track exact creation time dynamically,
            # but usually they are appended, so reversing gives roughly "newest first"
            # If we add created_at, we can do sort(key=lambda p: p.metadata.created_at, reverse=True)
            # For now, we will sort alphabetically descending as a proxy
            # In real system, we should have a timestamp, but let's assume we sort reversed
            # the list. The list is normally ordered by addition time from json backend.
            return list(reversed(patterns))

        elif sort_by == "usage":
            # Highest version counts as simplest proxy for usage if usage_stats are absent.
            # Real usage stats can be added later as an extension.
            return sorted(patterns, key=lambda p: p.metadata.version, reverse=True)

        else:
            # Default: Alphabetical by name
            return sorted(patterns, key=lambda p: p.name.lower())
