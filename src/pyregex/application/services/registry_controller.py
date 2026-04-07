from typing import List, Tuple
from pyregex.infrastructure.registry.schema.models import (
    RegistryPattern,
    PatternMetadata,
)
from pyregex.infrastructure.registry.validation.validator import RegistryValidator
from pyregex.infrastructure.registry.storage.json_backend import JsonStorageBackend
from pyregex.infrastructure.registry.indexing.indexer import MemoryIndexer
from pyregex.infrastructure.registry.search.engine import SearchEngine
from pyregex.infrastructure.registry.tagging.manager import TagManager
from pyregex.infrastructure.registry.versioning.tracker import VersionTracker

from pyregex.infrastructure.registry.commands.list.controller.list_controller import (
    ListController,
)
from pyregex.infrastructure.registry.commands.list.query.builder import ListQuery

from pyregex.infrastructure.registry.commands.delete.controller.delete_controller import (
    DeleteController,
)


class RegistryController:
    """Central entrypoint for the Persistent Registry System."""

    def __init__(self):
        self.validator = RegistryValidator()
        self.backend = JsonStorageBackend()
        self.indexer = MemoryIndexer()
        self.search_engine = SearchEngine(self.indexer)
        self.tag_manager = TagManager()
        self.version_tracker = VersionTracker()
        self.list_system = ListController(self.search_engine)
        self.delete_system = DeleteController(
            self.backend, self.indexer, self.search_engine
        )

        # Hydrate the memory index
        patterns = self.backend.get_all()
        self.indexer.build_index(patterns)

    def save(
        self,
        name: str,
        pattern: str,
        description: str = "",
        tags: List[str] | None = None,
        origin: str = "manual",
    ) -> Tuple[bool, List[str], RegistryPattern | None]:
        """Saves a rich pattern to the registry. Returns (success, errors, constructed_pattern)."""
        tags = tags or []

        # 1. Validation
        is_valid, errors = self.validator.validate(name, pattern)
        if not is_valid:
            return False, errors, None

        # 2. Tagging (Auto-suggestion)
        suggested_tags, category = self.tag_manager.suggest_metadata(pattern, tags)

        # 3. Versioning
        existing = self.backend.get(name)
        final_name = self.version_tracker.resolve_name_conflict(name, existing)
        version = (
            self.version_tracker.calculate_next_version(existing) if existing else 1
        )

        # Assemble Model
        meta = PatternMetadata(
            description=description,
            tags=suggested_tags,
            category=category,
            version=version,
            origin=origin,
        )
        registry_pattern = RegistryPattern(
            name=final_name, pattern=pattern, metadata=meta
        )

        # 4. Store
        self.backend.save(registry_pattern)

        # 5. Index
        self.indexer.add_to_index(registry_pattern)

        return True, [], registry_pattern

    def get_all(self, tag: str | None = None) -> List[RegistryPattern]:
        return self.search_engine.search_all(tag=tag)

    def search(self, keyword: str) -> List[RegistryPattern]:
        return self.search_engine.search_all(keyword=keyword)

    def list(self, query: ListQuery) -> str:
        """Entrypoint for the robust discovery subsystem."""
        return self.list_system.execute(query)

    def delete(self, name: str, force: bool = False) -> str:
        """Entrypoint for safe deletion."""
        return self.delete_system.request_delete(name, force)
