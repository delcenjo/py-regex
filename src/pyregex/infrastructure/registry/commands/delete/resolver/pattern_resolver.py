from typing import List, Optional, Tuple
from pyregex.infrastructure.registry.schema.models import RegistryPattern
from pyregex.infrastructure.registry.search.engine import SearchEngine


class PatternResolver:
    """Handles identification and fuzzy resolution of deletion targets."""

    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    def resolve(
        self, target_name: str
    ) -> Tuple[Optional[RegistryPattern], List[RegistryPattern]]:
        """
        Attempts to resolve a pattern name.
        Returns (ExactMatch, [Suggestions]).
        If ExactMatch is found, Suggestions may be empty.
        If ExactMatch is None, Suggestions contains fuzzy matches.
        """
        all_patterns = self.search_engine.search_all()

        # 1. Exact Match Check
        exact = next(
            (p for p in all_patterns if p.name.lower() == target_name.lower()), None
        )
        if exact:
            return exact, []

        # 2. Fuzzy Suggestions (Substring or Difflib)
        import difflib

        # Exact substring matches first
        suggestions = [
            p
            for p in all_patterns
            if target_name.lower() in p.name.lower()
            and p.name.lower() != target_name.lower()
        ]

        # If no substring matches, try difflib
        if not suggestions:
            names = [p.name for p in all_patterns]
            close_names = difflib.get_close_matches(
                target_name.lower(), [n.lower() for n in names], n=3, cutoff=0.4
            )

            for close_name in close_names:
                for p in all_patterns:
                    if p.name.lower() == close_name:
                        if p not in suggestions:
                            suggestions.append(p)
                        break

        return None, suggestions[:3]
