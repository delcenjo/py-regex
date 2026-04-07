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

        # 1. Erase from Backend Storage
        self.backend.delete(pattern.name)

        # 2. Re-hydrate/Clean Memory Index
        # To be safe, memory indexer might need a purge. The indexer currently accepts 'add'
        # but we can re-hydrate entirely from backend, or carefully remove keys.
        # For 100% consistency, wiping the index and reloading backend is safest at scale < 50,000.

        self.indexer.name_index.clear()
        self.indexer.tag_index.clear()
        self.indexer.category_index.clear()

        remaining_patterns = self.backend.get_all()
        for p in remaining_patterns:
            self.indexer.add_to_index(p)
