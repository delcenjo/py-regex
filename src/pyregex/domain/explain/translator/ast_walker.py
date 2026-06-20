from __future__ import annotations
from typing import List
from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    LiteralNode,
    DotNode,
    AnchorNode,
    CharClassNode,
    AlternationNode,
    SetClassNode,
    RangeNode,
    GroupNode,
    QuantifierNode,
    BackreferenceNode,
    FlagNode,
)


class NarrativeTranslator:
    """Visits AST nodes to generate a cohesive human-language narrative."""

    def __init__(self, root: RootNode):
        self.root = root

    def translate(self) -> List[str]:
        """Returns a list of sentences explaining the Regex."""
        self.narrative = []
        for child in self.root.children:
            self.narrative.append(self._visit(child))
        return self.narrative

    def _visit(self, node: AstNode) -> str:
        if isinstance(node, RootNode):
            return " ".join([self._visit(c) for c in node.children])

        if isinstance(node, LiteralNode):
            return f"Busca exactamente el texto '{node.value}'."

        if isinstance(node, DotNode):
            return (
                "Coincide con cualquier carácter (excepto saltos de línea por defecto)."
            )

        if isinstance(node, AnchorNode):
            if node.type == "start":
                return "Asegura que la coincidencia comienza al principio de la cadena."
            if node.type == "end":
                return "Asegura que la coincidencia termina al final de la cadena."
            if node.type == "word_boundary":
                return "Asegura que estamos en el límite de una palabra."
            return f"Anclaje: {node.value}"

        if isinstance(node, QuantifierNode):
            child_text = self._visit(node.child)
            mode = (
                "codicioso (intenta coincidir lo máximo posible)"
                if node.greedy
                else "perezoso (intenta coincidir lo menos posible)"
            )

            if node.min == 0 and node.max is None:
                freq = "cero o más veces"
            elif node.min == 1 and node.max is None:
                freq = "una o más veces"
            elif node.min == 0 and node.max == 1:
                freq = "cero o una vez (opcional)"
            elif node.max is None:
                freq = f"al menos {node.min} veces"
            elif node.min == node.max:
                freq = f"exactamente {node.min} veces"
            else:
                freq = f"entre {node.min} y {node.max} veces"

            return f"Seguido por un grupo que se repite {freq} en modo {mode}, el cual: {child_text}"

        if isinstance(node, GroupNode):
            children_text = " ".join([self._visit(c) for c in node.children])
            header = ""
            if node.type == "capture":
                header = f"Captura el grupo{' llamado <' + node.name + '>' if node.name else ''}"
            elif node.type == "non_capture":
                header = "Agrupa visualmente sin guardar la captura"
            elif node.type == "lookahead":
                header = "Verifica hacia adelante que esté seguido por"
            elif node.type == "negative_lookahead":
                header = "Verifica hacia adelante que NO esté seguido por"
            elif node.type == "lookbehind":
                header = "Verifica hacia atrás que esté precedido por"
            elif node.type == "negative_lookbehind":
                header = "Verifica hacia atrás que NO esté precedido por"

            return f"{header} el siguiente bloque: [{children_text}]"

        if isinstance(node, AlternationNode):
            left = self._visit(node.left)
            right = self._visit(node.right)
            return f"Opciones: Permite coincidir EITHER ({left}) OR ({right})."

        if isinstance(node, SetClassNode):
            items_t_list = [self._visit(i) for i in node.items]
            items_t = ", ".join(items_t_list)
            if node.negated:
                return f"Busca cualquier carácter que NO SEA: {items_t}."
            return f"Busca alguno de estos caracteres: {items_t}."

        if isinstance(node, CharClassNode):
            if node.type == "digit":
                return (
                    "cualquier número (0-9)"
                    if not node.negated
                    else "cualquier carácter que no sea número"
                )
            if node.type == "word":
                return (
                    "cualquier carácter alfanumérico o guión bajo"
                    if not node.negated
                    else "cualquier carácter no verbal"
                )
            if node.type == "whitespace":
                return (
                    "cualquier espacio en blanco, tabulador o salto"
                    if not node.negated
                    else "cualquier carácter visible"
                )
            return f"Clase de caracteres: {node.value}"

        if isinstance(node, RangeNode):
            return f"rango de '{node.start}' a '{node.end}'"

        if isinstance(node, BackreferenceNode):
            return f"Verifica que el valor sea idéntico al grupo capturado anteriormente (referencia: {node.ref_id})."

        if isinstance(node, FlagNode):
            return f"Activa temporalmente los flags internos: (?{node.flags_added})"

        return f"Componente no mapeado: {type(node).__name__}"
