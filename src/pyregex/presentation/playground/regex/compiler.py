"""Playground — Safe Regex Compiler.

Compiles regex patterns with error handling, position tracking, and timeout.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import re
import time


@dataclass
class CompileResult:
    """Result of a compilation attempt."""

    success: bool
    pattern: Optional[re.Pattern] = None
    error: Optional[str] = None
    error_pos: Optional[int] = None  # character position of the error
    error_span: Optional[tuple[int, int]] = None  # (start, end) of problematic part
    compile_time_us: float = 0.0
    flags_used: int = 0
    group_count: int = 0
    named_groups: dict[str, int] = field(default_factory=dict)

    @property
    def has_groups(self) -> bool:
        return self.group_count > 0


class SafeCompiler:
    """
    Safe regex compiler with error extraction and metadata.

    Features:
    - Precise error position detection
    - Group counting and named group discovery
    - Compilation timing
    - Flag validation
    """

    # Flags that can be toggled
    AVAILABLE_FLAGS = {
        "i": re.IGNORECASE,
        "m": re.MULTILINE,
        "s": re.DOTALL,
        "x": re.VERBOSE,
        "a": re.ASCII,
        "u": re.UNICODE,
    }

    def compile(self, pattern: str, flags: int = 0) -> CompileResult:
        """
        Safely compile a regex pattern.

        Returns a CompileResult with success/error info, timing, and metadata.
        """
        if not pattern:
            return CompileResult(success=False, error="Empty pattern")

        start = time.perf_counter()
        try:
            compiled = re.compile(pattern, flags)
            elapsed = (time.perf_counter() - start) * 1_000_000

            return CompileResult(
                success=True,
                pattern=compiled,
                compile_time_us=elapsed,
                flags_used=flags,
                group_count=compiled.groups,
                named_groups=dict(compiled.groupindex),
            )
        except re.error as e:
            elapsed = (time.perf_counter() - start) * 1_000_000
            error_pos = getattr(e, "pos", None)
            error_span = None

            # Try to determine the problematic span
            if error_pos is not None:
                error_span = (max(0, error_pos - 1), min(len(pattern), error_pos + 2))

            return CompileResult(
                success=False,
                error=self._format_error(str(e)),
                error_pos=error_pos,
                error_span=error_span,
                compile_time_us=elapsed,
                flags_used=flags,
            )

    def validate(self, pattern: str, flags: int = 0) -> list[str]:
        """Quick validation — returns list of issues (empty = valid)."""
        issues: list[str] = []

        if not pattern:
            return ["El patrón está vacío"]

        result = self.compile(pattern, flags)
        if not result.success:
            issues.append(f"Error de sintaxis: {result.error}")
            return issues

        # Heuristic warnings
        if len(pattern) > 500:
            issues.append("Patrón muy largo — considere dividirlo")

        # Check for common mistakes
        if pattern.count("(") != pattern.count(")"):
            issues.append("Paréntesis desbalanceados")

        if ".+" in pattern or ".*" in pattern:
            if ".+?" not in pattern and ".*?" not in pattern:
                issues.append(
                    "Cuantificadores codiciosos (.+ .*) pueden causar backtracking"
                )

        # Nested quantifiers (ReDoS risk)
        nested = re.search(r"\([^)]*[+*][^)]*\)[+*]", pattern)
        if nested:
            issues.append("Cuantificadores anidados — riesgo de ReDoS")

        return issues

    def extract_groups(self, pattern: str, flags: int = 0) -> list[dict]:
        """Extract information about all capture groups."""
        result = self.compile(pattern, flags)
        if not result.success or not result.pattern:
            return []

        groups = []
        named = result.named_groups

        # Find group positions in the pattern string
        depth = 0
        group_num = 0
        i = 0
        while i < len(pattern):
            if pattern[i] == "\\" and i + 1 < len(pattern):
                i += 2
                continue
            if pattern[i] == "(":
                depth += 1
                is_capture = True
                name = None

                # Check if non-capturing or special
                if i + 1 < len(pattern) and pattern[i + 1] == "?":
                    if i + 2 < len(pattern):
                        next_char = pattern[i + 2]
                        if next_char in (":", "=", "!", "<"):
                            if (
                                next_char == "<"
                                and i + 3 < len(pattern)
                                and pattern[i + 3] not in ("=", "!")
                            ):
                                # Named group (?P<name>...)
                                is_capture = True
                            elif (
                                next_char == "P"
                                and i + 3 < len(pattern)
                                and pattern[i + 3] == "<"
                            ):
                                is_capture = True
                            else:
                                is_capture = False
                        else:
                            is_capture = False
                    else:
                        is_capture = False

                if is_capture:
                    group_num += 1
                    # Check if it's a named group
                    for gname, gnum in named.items():
                        if gnum == group_num:
                            name = gname
                            break

                    groups.append(
                        {
                            "number": group_num,
                            "name": name,
                            "position": i,
                            "depth": depth,
                        }
                    )
            elif pattern[i] == ")":
                depth = max(0, depth - 1)
            i += 1

        return groups

    @staticmethod
    def flags_from_string(flags_str: str) -> int:
        """Convert flag string like 'im' to integer flags."""
        result = 0
        for char in flags_str.lower():
            if char in SafeCompiler.AVAILABLE_FLAGS:
                result |= SafeCompiler.AVAILABLE_FLAGS[char]
        return result

    @staticmethod
    def flags_to_string(flags: int) -> str:
        """Convert integer flags to string like 'im'."""
        result = []
        for char, flag in SafeCompiler.AVAILABLE_FLAGS.items():
            if flags & flag:
                result.append(char)
        return "".join(result)

    def _format_error(self, error: str) -> str:
        """Format error message for display."""
        translations = {
            "nothing to repeat": "Nada que repetir (cuantificador sin objetivo)",
            "unbalanced parenthesis": "Paréntesis desbalanceados",
            "unterminated subpattern": "Subpatrón sin cerrar",
            "missing ), unterminated subpattern": "Falta ) — subpatrón sin cerrar",
            "bad character range": "Rango de caracteres inválido",
            "unterminated character set": "Conjunto de caracteres sin cerrar (falta ])",
            "bad escape": "Secuencia de escape inválida",
            "multiple repeat": "Repetición múltiple (ej: a**)",
            "invalid group reference": "Referencia de grupo inválida",
        }
        for en, es in translations.items():
            if en in error.lower():
                return es
        return error
