"""AliasResolver — Expands @alias tokens into real regex patterns.

Connects to the RegistryController to fetch saved patterns and provides
mixed-mode expansion (e.g., `^(@username) - (@ip)$` → real regex).
"""

from __future__ import annotations

import re
from typing import Optional, Any


# Matches @alias_name tokens
_ALIAS_RE = re.compile(r"@([a-zA-Z_][a-zA-Z0-9_-]*)")

# Matches sequences of @aliases joined by '+' (e.g., @a + @b + @c)
_COMPOSITION_RE = re.compile(r"@([a-zA-Z_][a-zA-Z0-9_-]*)(?:\s*\+\s*@([a-zA-Z_][a-zA-Z0-9_-]*))+")


class AliasResolver:
    """Resolves @alias references to their stored regex patterns."""

    def __init__(self, registry: Any):
        self._registry = registry
        self._cache: dict[str, tuple[str, str]] = {}  # name → (pattern, description)
        self._refresh()

    def _refresh(self) -> None:
        """Rebuild the alias cache from the registry."""
        self._cache.clear()
        try:
            for rp in self._registry.get_all():
                self._cache[rp.name] = (rp.pattern, rp.metadata.description)
        except Exception:
            pass  # Registry might be empty or broken — degrade gracefully

    def refresh(self) -> None:
        """Public API to force a cache refresh."""
        self._refresh()

    @property
    def aliases(self) -> dict[str, tuple[str, str]]:
        """Returns {name: (pattern, description)} for all saved patterns."""
        return dict(self._cache)

    def has_aliases(self, text: str) -> bool:
        """Returns True if the text contains any @alias tokens."""
        return bool(_ALIAS_RE.search(text))

    def expand(self, text: str) -> str:
        """Replace all @alias tokens with their real regex patterns.

        Supports 'God-Level' composition: @alias1 + @alias2 + @alias3
        which expands to (?:pattern1)(?:pattern2)(?:pattern3).
        """
        # Phase 1: Detect and expand recursive + compositions
        # We search specifically for @alias + @alias sequences
        composition_re = re.compile(r"(@[a-zA-Z_][a-zA-Z0-9_-]*(?:\s*\+\s*@[a-zA-Z_][a-zA-Z0-9_-]*)+)")

        def _expand_composition(match: re.Match) -> str:
            chain = match.group(0)
            parts = [p.strip() for p in chain.split("+")]
            expanded_parts = []
            for part in parts:
                name = part[1:]  # remove @
                if name in self._cache:
                    pattern = self._cache[name][0]
                    # Wrap in non-capturing group to preserve precedence
                    expanded_parts.append(f"(?:{pattern})")
                else:
                    expanded_parts.append(part)
            return "".join(expanded_parts)

        text = composition_re.sub(_expand_composition, text)

        # Phase 2: Expand individual @aliases
        def _replace_single(m: re.Match) -> str:
            name = m.group(1)
            if name in self._cache:
                return self._cache[name][0]
            return m.group(0)

        return _ALIAS_RE.sub(_replace_single, text)

    def get_alias_info(self, name: str) -> Optional[tuple[str, str]]:
        """Returns (pattern, description) for a given alias name, or None."""
        return self._cache.get(name)

    def get_expanded_display(self, text: str) -> str:
        """Returns a string showing the full result of the expansion."""
        expanded = self.expand(text)
        if expanded == text:
            return ""
        
        # Truncate if too long
        if len(expanded) > 80:
            expanded = expanded[:77] + "..."
            
        return f"Expansión: {expanded}"
