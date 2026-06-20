from __future__ import annotations
from typing import Optional
from pyregex.infrastructure.registry.schema.models import RegistryPattern


class VersionTracker:
    """Manages versioning logic when saving patterns that already exist."""

    def calculate_next_version(self, existing: RegistryPattern) -> int:
        return existing.metadata.version + 1

    def resolve_name_conflict(
        self, new_name: str, existing_pattern: Optional[RegistryPattern]
    ) -> str:
        """
        If a pattern exists, we might want to automatically save it as name_v2.
        For now, we return the decided name.
        """
        if not existing_pattern:
            return new_name

        return new_name
