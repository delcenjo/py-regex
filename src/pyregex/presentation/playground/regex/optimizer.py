"""Playground — Pattern Optimizer.

Analyzes regex patterns and suggests improvements for performance and readability.
"""

from __future__ import annotations
from dataclasses import dataclass
import re


@dataclass
class Suggestion:
    """A single optimization suggestion."""

    severity: str  # info, warning, error, critical
    category: str  # performance, readability, correctness, security
    title: str
    description: str
    original: str = ""  # the problematic part
    suggested: str = ""  # the improved version
    position: int = -1  # position in the pattern

    @property
    def icon(self) -> str:
        icons = {"info": "", "warning": "", "error": "", "critical": ""}
        return icons.get(self.severity, "")


class PatternOptimizer:
    """
    Analyzes regex patterns and generates optimization suggestions.

    Categories:
    - Performance: ReDoS, unnecessary backtracking, greedy vs lazy
    - Readability: simplification, named groups, verbose mode
    - Correctness: common mistakes, edge cases
    - Security: injection patterns, ReDoS vulnerabilities
    """

    def analyze(self, pattern: str) -> list[Suggestion]:
        """Analyze a pattern and return all suggestions."""
        suggestions: list[Suggestion] = []

        if not pattern:
            return suggestions

        suggestions.extend(self._check_performance(pattern))
        suggestions.extend(self._check_readability(pattern))
        suggestions.extend(self._check_correctness(pattern))
        suggestions.extend(self._check_security(pattern))

        severity_order = {"critical": 0, "error": 1, "warning": 2, "info": 3}
        suggestions.sort(key=lambda s: severity_order.get(s.severity, 4))

        return suggestions

    def _check_performance(self, pattern: str) -> list[Suggestion]:
        sugs: list[Suggestion] = []

        # Nested quantifiers (catastrophic backtracking)
        nested = re.findall(r"\([^)]*[+*][^)]*\)[+*]", pattern)
        for n in nested:
            sugs.append(
                Suggestion(
                    severity="critical",
                    category="performance",
                    title="Cuantificadores anidados — ReDoS",
                    description="Este patrón puede causar backtracking catastrófico (explosión exponencial). "
                    "Usa grupos atómicos o cuantificadores posesivos si es posible.",
                    original=n,
                    suggested="Usa (?:...) con cuantificadores no codiciosos o refactoriza",
                )
            )

        # .* or .+ without lazy quantifier
        greedy_dots = list(re.finditer(r"(?<!\\)\.\*(?!\?)", pattern))
        for m in greedy_dots:
            sugs.append(
                Suggestion(
                    severity="warning",
                    category="performance",
                    title="Cuantificador codicioso con .",
                    description="'.*' es codicioso y puede consumir demasiado texto. "
                    "Considera '.*?' (lazy) si solo necesitas el mínimo.",
                    original=".*",
                    suggested=".*?",
                    position=m.start(),
                )
            )

        greedy_plus = list(re.finditer(r"(?<!\\)\.\+(?!\?)", pattern))
        for m in greedy_plus:
            sugs.append(
                Suggestion(
                    severity="warning",
                    category="performance",
                    title="Cuantificador codicioso con .",
                    description="'.+' es codicioso. Considera '.+?' si posible.",
                    original=".+",
                    suggested=".+?",
                    position=m.start(),
                )
            )

        # Very long alternation
        alts = pattern.split("|")
        if len(alts) > 10:
            sugs.append(
                Suggestion(
                    severity="info",
                    category="performance",
                    title=f"Alternación muy larga ({len(alts)} opciones)",
                    description="Las alternaciones largas pueden ser lentas. "
                    "Considera usar conjuntos de caracteres [] o un trie.",
                )
            )

        # Redundant character class [a] -> a
        singles = re.findall(r"\[([^\]\\])\]", pattern)
        for s in singles:
            if s not in "^-":
                sugs.append(
                    Suggestion(
                        severity="info",
                        category="performance",
                        title=f"Clase de caracteres innecesaria [{s}]",
                        description=f"[{s}] se puede simplificar a {s}",
                        original=f"[{s}]",
                        suggested=s,
                    )
                )

        return sugs

    def _check_readability(self, pattern: str) -> list[Suggestion]:
        sugs: list[Suggestion] = []

        # Very long pattern without verbose mode
        if len(pattern) > 80 and "(?x)" not in pattern:
            sugs.append(
                Suggestion(
                    severity="info",
                    category="readability",
                    title="Patrón largo — considera modo verbose",
                    description="Con el flag (?x) puedes añadir comentarios y espacios "
                    "para hacer el patrón más legible.",
                )
            )

        # Capture groups that could be non-capturing
        captures = re.findall(r"\((?!\?)", pattern)
        if len(captures) > 3:
            sugs.append(
                Suggestion(
                    severity="info",
                    category="readability",
                    title=f"{len(captures)} grupos de captura",
                    description="Si no necesitas capturar todos los grupos, "
                    "usa (?:...) para los que no necesites.",
                )
            )

        # No named groups in complex pattern
        if len(captures) > 2 and "?P<" not in pattern and "?<" not in pattern:
            sugs.append(
                Suggestion(
                    severity="info",
                    category="readability",
                    title="Considera usar grupos con nombre",
                    description="Los grupos con nombre (?P<name>...) hacen "
                    "el código más legible y mantenible.",
                )
            )

        return sugs

    def _check_correctness(self, pattern: str) -> list[Suggestion]:
        sugs: list[Suggestion] = []

        if re.search(r"\w+@\w+", pattern) and "+" not in pattern:
            sugs.append(
                Suggestion(
                    severity="info",
                    category="correctness",
                    title="Patrón de email simplificado",
                    description="Los emails permiten +, . y otros caracteres "
                    "antes del @. Considera [a-zA-Z0-9._%+-]+",
                )
            )

        if pattern and pattern[0] != "^" and pattern[-1] != "$":
            if not any(pattern.startswith(p) for p in ["\\b", "(?:", "(?"]):
                sugs.append(
                    Suggestion(
                        severity="info",
                        category="correctness",
                        title="Sin anclas (^ $)",
                        description="El patrón puede matchear partes de texto no deseadas. "
                        "Añade ^ y $ si necesitas match completo, o \\b para word boundaries.",
                    )
                )

        return sugs

    def _check_security(self, pattern: str) -> list[Suggestion]:
        sugs: list[Suggestion] = []

        # Potential ReDoS with specific patterns
        redos_patterns = [
            (r"\(\.\*\)\+", "(.*)+ — exponential backtracking"),
            (r"\(\.\+\)\+", "(.+)+ — exponential backtracking"),
            (r"\([^)]*\|[^)]*\)\+", "(a|b)+ — alternation in quantified group"),
        ]

        for rx, desc in redos_patterns:
            if re.search(rx, pattern):
                sugs.append(
                    Suggestion(
                        severity="critical",
                        category="security",
                        title="Vulnerabilidad ReDoS detectada",
                        description=f"{desc}. Un atacante podría causar Denial "
                        "of Service con input malicioso.",
                    )
                )

        return sugs

    def format_suggestions(self, suggestions: list[Suggestion]) -> list[str]:
        """Format suggestions as displayable text."""
        if not suggestions:
            return ["  Sin sugerencias — patrón correcto"]

        lines = []
        for s in suggestions:
            lines.append(f"  {s.icon} [{s.category.upper()}] {s.title}")
            lines.append(f"    {s.description}")
            if s.original and s.suggested:
                lines.append(f"    {s.original} → {s.suggested}")
            lines.append("")

        return lines
