from typing import List, Dict, Any


class Paginator:
    """Handles pagination over list or grouped outputs."""

    @staticmethod
    def paginate_flat(items: List[Any], page: int, limit: int) -> Dict[str, Any]:
        start = (page - 1) * limit
        end = start + limit
        total = len(items)

        sliced = items[start:end]

        return {
            "items": sliced,
            "page": page,
            "limit": limit,
            "total": total,
            "has_next": end < total,
            "has_prev": page > 1,
        }
