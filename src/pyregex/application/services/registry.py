from typing import Dict, List, Optional

# Lazy load presets to avoid circularity if any
# (Though presets.py is just a dict)
from pyregex.application.services.audit.presets import PRESETS


class PatternRegistry:
    """Central registry for all regex patterns (entities).

    Provides a unified interface for Audit, Mask, Transform, and Validate
    to access patterns by name, tag, or category.
    """

    def __init__(self):
        self.entities: Dict[str, str] = {}
        self.tags: Dict[str, List[str]] = {}
        self._load_presets()

    def _load_presets(self):
        """Loads default patterns from presets.py."""
        for category, patterns in PRESETS.items():
            for name, pattern in patterns.items():
                self.register(name, pattern, [category])

    def register(self, name: str, pattern: str, tags: Optional[List[str]] = None):
        """Registers a new pattern in the registry."""
        name = name.upper()
        self.entities[name] = pattern
        if tags:
            for tag in tags:
                tag = tag.lower()
                if tag not in self.tags:
                    self.tags[tag] = []
                if name not in self.tags[tag]:
                    self.tags[tag].append(name)

    def get_pattern(self, name_or_tag: str) -> Optional[str]:
        """Returns a pattern by name or a combined pattern if it's a tag."""
        name_or_tag = name_or_tag.upper()
        if name_or_tag in self.entities:
            return self.entities[name_or_tag]

        tag = name_or_tag.lower()
        if tag in self.tags:
            # Combine all patterns in the tag into an OR group
            patterns = [self.entities[n] for n in self.tags[tag]]
            return "|".join(f"({p})" for p in patterns)

        return None

    def list_entities(self, tag: Optional[str] = None) -> List[str]:
        """Lists all registered entity names, filtered by tag."""
        if tag:
            return self.tags.get(tag.lower(), [])
        return list(self.entities.keys())

    def resolve_rule(self, rule_str: str) -> List[tuple[str, str]]:
        """Resolves a rule string like 'all', 'pii', or 'EMAIL' into (name, pattern) pairs."""
        if rule_str.lower() == "all":
            return [(name, pattern) for name, pattern in self.entities.items()]

        if rule_str.lower() in self.tags:
            tag = rule_str.lower()
            return [(name, self.entities[name]) for name in self.tags[tag]]

        pattern = self.get_pattern(rule_str)
        if pattern:
            return [(rule_str.upper(), pattern)]

        # If it looks like a regex, return it as a raw rule
        if any(c in rule_str for c in ".*+?[]^$()"):
            return [("CUSTOM", rule_str)]

        return []


# Global instance for easier access (can be overridden by Context)
registry = PatternRegistry()
