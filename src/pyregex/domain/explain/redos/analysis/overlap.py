"""Overlap Analyzer — Detects CharSet overlaps in alternations and quantifiers.

Works directly on the AST (no NFA needed) to find patterns where
two branches of an alternation, or a quantifier and its suffix,
accept the same characters — the root cause of polynomial backtracking.
"""

from __future__ import annotations
from typing import Optional

from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    LiteralNode,
    DotNode,
    CharClassNode,
    SetClassNode,
    RangeNode,
    AlternationNode,
    GroupNode,
    QuantifierNode,
)
from pyregex.domain.explain.redos.models import (
    CharSet,
    Vulnerability,
    VulnType,
    Severity,
)


class OverlapAnalyzer:
    """Detects character set overlaps that cause backtracking."""

    def analyze(self, root: RootNode) -> list[Vulnerability]:
        vulns: list[Vulnerability] = []
        self._walk(root, vulns)
        return vulns

    def _walk(self, node: AstNode, vulns: list[Vulnerability]):
        if isinstance(node, RootNode):
            self._check_sequence(node.children, vulns)
            for child in node.children:
                self._walk(child, vulns)

        elif isinstance(node, GroupNode):
            self._check_sequence(node.children, vulns)
            for child in node.children:
                self._walk(child, vulns)

        elif isinstance(node, AlternationNode):
            self._check_alternation(node, vulns)
            self._walk(node.left, vulns)
            self._walk(node.right, vulns)

        elif isinstance(node, QuantifierNode):
            self._walk(node.child, vulns)

    def _check_alternation(self, node: AlternationNode, vulns: list[Vulnerability]):
        """Check if branches of alternation accept overlapping chars."""
        cs_left = self._extract_charset(node.left)
        cs_right = self._extract_charset(node.right)

        if cs_left and cs_right and cs_left.intersects(cs_right):
            overlap = cs_left & cs_right
            vulns.append(
                Vulnerability(
                    type=VulnType.ALTERNATION_OVERLAP,
                    severity=Severity.MEDIUM,
                    description=(
                        f"Alternación con {overlap.count()} caracteres comunes "
                        f"entre ramas — puede causar backtracking"
                    ),
                    explanation=(
                        "Cuando ambas ramas de una alternación aceptan los mismos "
                        "caracteres, el motor debe probar ambas. Con un cuantificador "
                        "encima, esto causa O(N²) o peor."
                    ),
                    fix_suggestion="Fusiona las ramas en un solo conjunto de caracteres",
                )
            )

    def _check_sequence(self, children: list[AstNode], vulns: list[Vulnerability]):
        """Check adjacent elements in a sequence for overlapping quantifiers."""
        for i in range(len(children) - 1):
            curr = children[i]
            nxt = children[i + 1]

            if isinstance(curr, QuantifierNode):
                cs_quant = self._extract_charset(curr.child)
                cs_next = self._extract_charset(nxt)

                if cs_quant and cs_next and cs_quant.intersects(cs_next):
                    is_infinite = curr.max is None
                    overlap = cs_quant & cs_next

                    if isinstance(nxt, QuantifierNode) and is_infinite:
                        vulns.append(
                            Vulnerability(
                                type=VulnType.ADJACENT_OVERLAP,
                                severity=Severity.HIGH,
                                description=(
                                    f"Cuantificadores adyacentes con {overlap.count()} "
                                    f"caracteres comunes — causa O(N²) mínimo"
                                ),
                                explanation=(
                                    "Dos cuantificadores infinitos adyacentes que aceptan "
                                    "los mismos caracteres compiten por cada carácter. "
                                    "El motor prueba todas las particiones posibles."
                                ),
                                fix_suggestion="Fusiona en un solo cuantificador",
                            )
                        )
                    elif is_infinite:
                        vulns.append(
                            Vulnerability(
                                type=VulnType.QUANTIFIER_SUFFIX_OVERLAP,
                                severity=Severity.MEDIUM,
                                description=(
                                    f"Cuantificador seguido de elemento con "
                                    f"{overlap.count()} caracteres comunes"
                                ),
                                explanation=(
                                    "El cuantificador puede 'tragarse' el carácter "
                                    "que necesita el siguiente elemento, forzando "
                                    "retrocesos."
                                ),
                                fix_suggestion="Usa un lookahead o reordena el patrón",
                            )
                        )

    def _extract_charset(self, node: AstNode) -> Optional[CharSet]:
        """Extract the CharSet a node can match (first character)."""
        if isinstance(node, LiteralNode):
            if node.value:
                return CharSet.from_char(node.value[0])
            return None

        if isinstance(node, DotNode):
            return CharSet.dot()

        if isinstance(node, CharClassNode):
            return self._resolve_charclass(node)

        if isinstance(node, SetClassNode):
            cs = CharSet()
            for item in node.items:
                if isinstance(item, LiteralNode) and item.value:
                    cs = cs | CharSet.from_char(item.value[0])
                elif isinstance(item, RangeNode):
                    cs = cs | CharSet.from_range(item.start, item.end)
                elif isinstance(item, CharClassNode):
                    r = self._resolve_charclass(item)
                    if r:
                        cs = cs | r
            if node.negated:
                cs = ~cs
            return cs if cs else None

        if isinstance(node, QuantifierNode):
            return self._extract_charset(node.child)

        if isinstance(node, GroupNode):
            if node.children:
                return self._extract_charset(node.children[0])
            return None

        if isinstance(node, AlternationNode):
            left = self._extract_charset(node.left)
            right = self._extract_charset(node.right)
            if left and right:
                return left | right
            return left or right

        if isinstance(node, RootNode):
            if node.children:
                return self._extract_charset(node.children[0])
            return None

        return None

    @staticmethod
    def _resolve_charclass(node: CharClassNode) -> Optional[CharSet]:
        base_map = {
            "digit": CharSet.digit,
            "word": CharSet.word,
            "whitespace": CharSet.whitespace,
        }
        factory = base_map.get(node.type)
        if factory:
            cs = factory()
            return ~cs if node.negated else cs
        return None
