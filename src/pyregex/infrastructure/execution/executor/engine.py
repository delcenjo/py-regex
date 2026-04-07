from dataclasses import dataclass
from typing import Dict, Generator
import re
from pyregex.infrastructure.registry.schema.models import RegistryPattern
from pyregex.infrastructure.execution.target_loader.loader import BaseLoader


@dataclass
class MatchResult:
    source: str
    line_number: int
    full_string: str
    match_start: int
    match_end: int
    matched_text: str
    groups: Dict[int, str]
    named_groups: Dict[str, str]


class ExecutionEngine:
    """Core Regex compiler and applicator."""

    def __init__(self, pattern: RegistryPattern):
        self.pattern = pattern

        # Determine internal flags (like ignores, multiline) from metadata if we store it
        # For now, default compile
        try:
            self.compiled_regex = re.compile(pattern.pattern)
        except re.error as e:
            raise ValueError(
                f"Pattern '{pattern.name}' contains invalid regex syntax: {e}"
            )

    def execute_stream(
        self, loader: BaseLoader, apply_global: bool = True
    ) -> Generator[MatchResult, None, None]:
        """
        Consumes the target stream and yields highly structured MatchResult objects.
        If apply_global is True, runs 'finditer'. If False, runs 'search'.
        """
        for source, chunk, line_num in loader.stream_chunks():
            if apply_global:
                matches = self.compiled_regex.finditer(chunk)
                for match in matches:
                    yield self._build_result(source, line_num, chunk, match)
            else:
                match = self.compiled_regex.search(chunk)
                if match:
                    yield self._build_result(source, line_num, chunk, match)

    def _build_result(
        self, source: str, line_num: int, chunk: str, match: re.Match
    ) -> MatchResult:
        """Constructs the pro-tier dataclass."""
        groups = {
            i: match.group(i)
            for i in range(1, len(match.groups()) + 1)
            if match.group(i)
        }
        named_groups = {k: v for k, v in match.groupdict().items() if v}

        return MatchResult(
            source=source,
            line_number=line_num,
            full_string=chunk,
            match_start=match.start(),
            match_end=match.end(),
            matched_text=match.group(0),
            groups=groups,
            named_groups=named_groups,
        )
