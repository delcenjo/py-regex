from typing import List
from pyregex.infrastructure.registry.schema.models import RegistryPattern
from pyregex.infrastructure.registry.indexing.indexer import MemoryIndexer


class SearchEngine:
    """Performs queries against the MemoryIndexer."""

    def __init__(self, indexer: MemoryIndexer):
        self.indexer = indexer

    def find_by_name(self, name: str) -> RegistryPattern | None:
        return self.indexer.name_index.get(name)

    def find_by_tag(self, tag: str) -> List[RegistryPattern]:
        names = self.indexer.tag_index.get(tag, set())
        return [self.indexer.name_index[name] for name in names]

    def find_by_category(self, category: str) -> List[RegistryPattern]:
        names = self.indexer.category_index.get(category, set())
        return [self.indexer.name_index[name] for name in names]

    def search_all(self, keyword: str | None = None, tag: str | None = None) -> List[RegistryPattern]:
        """A generic search that optionally filters by a global keyword and/or a specific tag."""
        results = []
        if tag:
            results = self.find_by_tag(tag)
        else:
            results = list(self.indexer.name_index.values())

        if keyword:
            keyword = keyword.lower()
            filtered = []
            for p in results:
                # Search name, description, tags, pattern
                parts = [
                    p.name.lower(),
                    p.metadata.description.lower(),
                    p.pattern.lower(),
                ]
                parts.extend([t.lower() for t in p.metadata.tags])
                if any(keyword in part for part in parts):
                    filtered.append(p)
            results = filtered

        return sorted(results, key=lambda x: x.name)
