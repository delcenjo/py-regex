from typing import List, Dict
from pyregex.infrastructure.registry.schema.models import RegistryPattern


class Grouper:
    """Groups patterns into hierarchical structures."""

    @staticmethod
    def group(
        patterns: List[RegistryPattern], group_by: str | None
    ) -> Dict[str, List[RegistryPattern]]:
        """
        Groups patterns.
        Returns a dictionary. If group_by is None, returns a flat dict with a 'results' key.
        """
        grouped = {}

        if not group_by:
            return {"results": patterns}

        if group_by == "category":
            for p in patterns:
                cat = p.metadata.category
                if cat not in grouped:
                    grouped[cat] = []
                grouped[cat].append(p)

        elif group_by == "tag":
            for p in patterns:
                # If no tags, bucket into untagged
                if not p.metadata.tags:
                    grouped.setdefault("untagged", []).append(p)
                else:
                    # A pattern might appear in multiple tag buckets
                    for tag in p.metadata.tags:
                        grouped.setdefault(tag, []).append(p)

        return grouped
