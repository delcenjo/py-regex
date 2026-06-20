from pyregex.infrastructure.registry.commands.list.query.builder import ListQuery
from pyregex.infrastructure.registry.commands.list.filtering.filter_engine import (
    FilterEngine,
)
from pyregex.infrastructure.registry.commands.list.sorting.sorter import Sorter
from pyregex.infrastructure.registry.commands.list.grouping.grouper import Grouper
from pyregex.infrastructure.registry.commands.list.pagination.paginator import Paginator
from pyregex.infrastructure.registry.commands.list.output.views import (
    SimpleView,
    DetailedView,
    CompactView,
    GroupedView,
)
from pyregex.infrastructure.registry.search.engine import SearchEngine
from pyregex.utils import ansi


class ListController:
    """Orchestrates the discovery subsystem pipeline."""

    def __init__(self, search_engine: SearchEngine):
        self.filter_engine = FilterEngine(search_engine)
        self.sorter = Sorter()
        self.grouper = Grouper()
        self.paginator = Paginator()

        self.views = {
            "simple": SimpleView(),
            "compact": CompactView(),
            "detailed": DetailedView(),
            "tree": GroupedView(),
        }

    def execute(self, query: ListQuery) -> str:
        patterns = self.filter_engine.execute(query)
        sorted_patterns = self.sorter.sort(patterns, query.sort_by)
        grouped_data = self.grouper.group(sorted_patterns, query.group_by)

        if query.group_by:
            # Pass the full dict to tree views to avoid disjointed category headers
            pagination_data = {
                "items": grouped_data,
                "total": len(sorted_patterns),
                "page": 1,
                "limit": query.limit,
                "has_next": False,
            }
        else:
            flat_list = grouped_data.get("results", [])
            pagination_data = self.paginator.paginate_flat(
                flat_list, query.page, query.limit
            )

        view = self.views.get(query.view_mode, self.views["simple"])

        if query.group_by and query.view_mode != "tree":
            view = self.views["tree"]
        elif not query.group_by and query.view_mode == "tree":
            view = self.views["simple"]

        rendered = view.render(pagination_data)

        footer = ""
        total = pagination_data.get("total", 0)
        if total > 0 and not query.group_by:
            footer = f"\n{ansi.dim(f'Showing {len(pagination_data.get('items', []))} of {total} patterns.')}"

        return rendered + footer
