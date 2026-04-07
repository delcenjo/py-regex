from typing import List, Dict, Set
from pyregex.infrastructure.registry.schema.models import RegistryPattern


class MemoryIndexer:
    """Provides high-speed memory indexing for fast lookups."""

    def __init__(self):
        self.name_index: Dict[str, RegistryPattern] = {}
        self.tag_index: Dict[str, Set[str]] = {}
        self.category_index: Dict[str, Set[str]] = {}

    def build_index(self, patterns: List[RegistryPattern]) -> None:
        self.name_index.clear()
        self.tag_index.clear()
        self.category_index.clear()

        for p in patterns:
            self.name_index[p.name] = p

            for tag in p.metadata.tags:
                if tag not in self.tag_index:
                    self.tag_index[tag] = set()
                self.tag_index[tag].add(p.name)

            cat = p.metadata.category
            if cat not in self.category_index:
                self.category_index[cat] = set()
            self.category_index[cat].add(p.name)

    def add_to_index(self, pattern: RegistryPattern) -> None:
        self.name_index[pattern.name] = pattern
        for tag in pattern.metadata.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = set()
            self.tag_index[tag].add(pattern.name)

        cat = pattern.metadata.category
        if cat not in self.category_index:
            self.category_index[cat] = set()
        self.category_index[cat].add(pattern.name)

    def remove_from_index(self, name: str) -> None:
        p = self.name_index.pop(name, None)
        if not p:
            return

        for tag in p.metadata.tags:
            if tag in self.tag_index:
                self.tag_index[tag].discard(name)

        cat = p.metadata.category
        if cat in self.category_index:
            self.category_index[cat].discard(name)
