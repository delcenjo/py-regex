from typing import Optional, List, Any, Tuple


class LegacyRegistryAdapter:
    """
    Bridge wrapper allowing legacy systems (MergeService, SecurityService, Audit, Mask, etc)
    to interact with the new RegistryController until they undergo their Phase rewrites.
    """

    def __init__(self):
        self._controller_instance = None
        
    @property
    def _controller(self):
        if self._controller_instance is None:
            from pyregex.application.services.registry_controller import RegistryController
            self._controller_instance = RegistryController()
        return self._controller_instance

    def register(self, name: str, pattern: str, tags: Optional[List[str]] = None):
        self._controller.save(name=name, pattern=pattern, tags=tags)

    def get_pattern(self, name: str) -> Optional[str]:
        # Returns raw pattern string for backward compatibility
        model = self._controller.backend.get(name)
        return model.pattern if model else None

    def list_entities(self, tag: Optional[str] = None) -> List[str]:
        # Legacy list_entities returned list of names based on tag filters
        patterns = self._controller.get_all(tag=tag)
        return [m.name for m in patterns]

    def resolve_rule(self, name: str) -> List[Tuple[str, str]]:
        """Resolve a rule name (tag or pattern name) into a list of (name, pattern) tuples."""
        # First try as a tag
        tagged = self._controller.get_all(tag=name)
        if tagged:
            return [(m.name, m.pattern) for m in tagged]

        # Then try as a specific pattern name
        pat = self.get_pattern(name)
        if pat:
            return [(name, pat)]

        # If 'all', return everything
        if name.lower() == "all":
            all_patterns = self._controller.backend.get_all()
            return [(m.name, m.pattern) for m in all_patterns]

        return []

    @property
    def entities(self):
        return {m.name: m for m in self._controller.backend.get_all()}

    @property
    def tags(self):
        # Flatten all tags from all models
        t = set()
        for m in self._controller.backend.get_all():
            t.update(m.metadata.tags)
        return list(t)


# Export legacy singleton
registry = LegacyRegistryAdapter()
