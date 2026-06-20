from pyregex.infrastructure.registry.schema.models import RegistryPattern
from pyregex.infrastructure.registry.storage.backend import StorageBackend
from pyregex.infrastructure.registry.indexing.indexer import MemoryIndexer


class Deleter:
    """Perform actual memory and storage deletion."""

    def __init__(self, backend: StorageBackend, indexer: MemoryIndexer):
        self.backend = backend
        self.indexer = indexer

    def execute(self, pattern: RegistryPattern):
        """Permanently removes the pattern from the core registry and memory."""

        self.backend.delete(pattern.name)

        # Rebuild the in-memory index from the remaining backend entries.
        self.indexer.name_index.clear()
        self.indexer.tag_index.clear()
        self.indexer.category_index.clear()

        remaining_patterns = self.backend.get_all()
        for p in remaining_patterns:
            self.indexer.add_to_index(p)
