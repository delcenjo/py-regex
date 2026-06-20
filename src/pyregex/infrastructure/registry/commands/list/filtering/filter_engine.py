from typing import List
from pyregex.infrastructure.registry.schema.models import RegistryPattern
from pyregex.infrastructure.registry.commands.list.query.builder import ListQuery
from pyregex.infrastructure.registry.search.engine import SearchEngine


class FilterEngine:
    """Uses the ListQuery to extract matching data from the SearchEngine."""

    def __init__(self, search_engine: SearchEngine):
        self.search_engine = search_engine

    def execute(self, query: ListQuery) -> List[RegistryPattern]:
        patterns = self.search_engine.search_all(
            keyword=query.keyword, tag=query.tag_filter
        )

        if query.category_filter:
            target = query.category_filter.lower()
            patterns = [p for p in patterns if p.metadata.category == target]

        return patterns
