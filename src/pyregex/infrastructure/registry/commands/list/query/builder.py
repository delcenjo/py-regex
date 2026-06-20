from dataclasses import dataclass
from typing import Optional


@dataclass
class ListQuery:
    """Represents the user's intent when exploring the registry."""

    keyword: Optional[str] = None
    tag_filter: Optional[str] = None
    category_filter: Optional[str] = None
    sort_by: str = "name"  # "name", "created", "usage"
    group_by: Optional[str] = None  # "category", "tag", None
    view_mode: str = "simple"  # "simple", "detailed", "compact", "tree"
    page: int = 1
    limit: int = 50


class QueryBuilder:
    """Fluent builder for constructing ListQueries."""

    def __init__(self):
        self._query = ListQuery()

    def with_keyword(self, keyword: str):
        if keyword:
            self._query.keyword = keyword
        return self

    def with_tag(self, tag: str):
        if tag:
            self._query.tag_filter = tag
        return self

    def with_category(self, category: str):
        if category:
            self._query.category_filter = category
        return self

    def sort_by(self, field: str):
        if field in ["name", "created", "usage"]:
            self._query.sort_by = field
        return self

    def group_by(self, field: str):
        if field in ["category", "tag"]:
            self._query.group_by = field
        return self

    def view_as(self, mode: str):
        if mode in ["simple", "detailed", "compact", "tree"]:
            self._query.view_mode = mode
        return self

    def paginate(self, page: int, limit: int):
        self._query.page = max(1, page)
        self._query.limit = max(1, limit)
        return self

    def build(self) -> ListQuery:
        return self._query
