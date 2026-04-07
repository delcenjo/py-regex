from __future__ import annotations
import json
import csv
import io
from typing import Any, Dict, List, Optional
from pyregex.application.services.engine import RegexEngine


class ExtractService:
    """Service for extracting structured data from text using regex engines."""

    def __init__(self, engine: RegexEngine):
        self.engine = engine

    def extract(
        self,
        text: str,
        output_format: str = "text",
        unique: bool = False,
        include_count: bool = False,
        group_by: Optional[str] = None,
    ) -> str:
        """Extracts data and returns it in the requested format."""
        matches = list(self.engine.finditer(text))

        # 1. Transform matches to raw data
        results = []
        for m in matches:
            res = {
                "match": m.group(),
                "start": m.start(),
                "end": m.end(),
                "groups": m.groupdict() if m.groupdict() else list(m.groups()),
            }
            results.append(res)

        # 2. Apply aggregations
        if unique or include_count or group_by:
            results = self._aggregate(results, unique, include_count, group_by)

        # 3. Format output
        if output_format == "json":
            return self._to_json(results)
        elif output_format == "csv":
            return self._to_csv(results)
        else:
            return self._to_text(results, include_count)

    def _aggregate(
        self,
        results: List[Dict[str, Any]],
        unique: bool,
        include_count: bool,
        group_by: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Handles uniqueness, counting, and grouping."""
        aggregated: Dict[str, Dict[str, Any]] = {}

        for res in results:
            # Determine the key for aggregation
            if group_by:
                # If grouping by a specific named group
                if isinstance(res["groups"], dict) and group_by in res["groups"]:
                    key = str(res["groups"][group_by])
                else:
                    key = res["match"]  # Fallback to full match
            else:
                key = res["match"]

            if key not in aggregated:
                aggregated[key] = {"match": key, "count": 1, "first_occurrence": res}
            else:
                aggregated[key]["count"] += 1

        final_results = []
        for key, data in aggregated.items():
            item = data["first_occurrence"].copy()
            if include_count:
                item["count"] = data["count"]
            final_results.append(item)

        if unique:
            return final_results

        # If not unique but we wanted counts, we usually want the unique set with counts
        if include_count:
            return final_results

        # If neither unique nor count, but group_by was used, it's essentially unique by that key
        if group_by:
            return final_results

        return results

    def _to_json(self, results: List[Dict[str, Any]]) -> str:
        return json.dumps(results, indent=2)

    def _to_csv(self, results: List[Dict[str, Any]]) -> str:
        if not results:
            return ""

        output = io.StringIO()
        # Find all keys including nested groups if they are dicts
        fieldnames = ["match", "start", "end"]
        if "count" in results[0]:
            fieldnames.append("count")

        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
        return output.getvalue()

    def _to_text(self, results: List[Dict[str, Any]], include_count: bool) -> str:
        lines = []
        for res in results:
            line = res["match"]
            if include_count:
                line = f"{res.get('count', 1)}: {line}"
            lines.append(line)
        return "\n".join(lines)
