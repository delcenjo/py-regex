from typing import List
import json
import csv
import io
from pyregex.infrastructure.execution.executor.engine import MatchResult
from pyregex.utils import ansi


class OutputFormatter:
    """Handles visual console display and export serializations."""

    def format_ansi(self, results: List[MatchResult]) -> str:
        """Renders rich terminal colors."""
        if not results:
            return ansi.dim("No matches found.")

        output = []
        for r in results:
            # Highlight the precise match substring inside the full string chunk
            prefix = r.full_string[: r.match_start]
            match_str = r.full_string[r.match_start : r.match_end]
            suffix = r.full_string[r.match_end :]

            colored_chunk = f"{prefix}{ansi.highlight(match_str)}{suffix}"
            loc = ansi.dim(f"[{r.source}:{r.line_number}]")
            output.append(f"{loc} -> {colored_chunk}")

        return "\n".join(output)

    def format_json(self, results: List[MatchResult]) -> str:
        dicts = []
        for r in results:
            dicts.append(
                {
                    "source": r.source,
                    "line": r.line_number,
                    "match": r.matched_text,
                    "groups": r.groups,
                    "named_groups": r.named_groups,
                }
            )
        return json.dumps(dicts, indent=2)

    def format_csv(self, results: List[MatchResult]) -> str:
        if not results:
            return "source,line,match"

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["source", "line", "match"])
        for r in results:
            writer.writerow([r.source, r.line_number, r.matched_text])
        return output.getvalue().strip()
