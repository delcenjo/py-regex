"""NFA Builder — Converts AST to NFA graph via Thompson construction.

Uses the dataclass-based AST from ``models/ast.py`` (the one produced
by ``RecursiveDescentParser``).
"""

from __future__ import annotations

from pyregex.domain.explain.models.ast import (
    AstNode,
    RootNode,
    LiteralNode,
    DotNode,
    AnchorNode,
    CharClassNode,
    SetClassNode,
    RangeNode,
    AlternationNode,
    GroupNode,
    QuantifierNode,
    BackreferenceNode,
    FlagNode,
)
from pyregex.domain.explain.redos.models import (
    NFAState,
    NFAFragment,
    CharSet,
)
from pyregex.domain.explain.redos.nfa.fragment import (
    StateAllocator,
    frag_char,
    frag_epsilon,
    frag_concat,
    frag_alternate,
    frag_repeat,
)


class NFABuilder:
    """Builds an NFA graph from a parsed regex AST.

    Returns ``(start_state, accept_state, state_count)`` so the
    simulator can walk the graph.
    """

    def __init__(self):
        self.alloc = StateAllocator()

    def build(self, root: RootNode) -> tuple[NFAState, NFAState, int]:
        """Build complete NFA from AST root.

        Returns (start, accept, state_count).
        """
        frag = self._visit(root)
        frag.end.is_accept = True
        return frag.start, frag.end, self.alloc.count

    # ── Dispatcher ────────────────────────────────────────────────

    def _visit(self, node: AstNode) -> NFAFragment:
        if isinstance(node, RootNode):
            return self._visit_root(node)
        if isinstance(node, LiteralNode):
            return self._visit_literal(node)
        if isinstance(node, DotNode):
            return self._visit_dot(node)
        if isinstance(node, CharClassNode):
            return self._visit_charclass(node)
        if isinstance(node, SetClassNode):
            return self._visit_setclass(node)
        if isinstance(node, AlternationNode):
            return self._visit_alternation(node)
        if isinstance(node, GroupNode):
            return self._visit_group(node)
        if isinstance(node, QuantifierNode):
            return self._visit_quantifier(node)
        if isinstance(node, AnchorNode):
            return frag_epsilon(self.alloc)  # anchors don't consume input
        if isinstance(node, BackreferenceNode):
            return frag_epsilon(self.alloc)  # can't model backrefs in NFA
        if isinstance(node, FlagNode):
            return frag_epsilon(self.alloc)
        # Fallback for unknown nodes
        return frag_epsilon(self.alloc)

    # ── Visitors ──────────────────────────────────────────────────

    def _visit_root(self, node: RootNode) -> NFAFragment:
        if not node.children:
            return frag_epsilon(self.alloc)
        return self._concat_children(node.children)

    def _visit_literal(self, node: LiteralNode) -> NFAFragment:
        # Each character in the literal gets its own state
        if not node.value:
            return frag_epsilon(self.alloc)

        result: NFAFragment | None = None
        for ch in node.value:
            f = frag_char(self.alloc, CharSet.from_char(ch))
            result = frag_concat(result, f) if result else f
        return result  # type: ignore

    def _visit_dot(self, node: DotNode) -> NFAFragment:
        cs = CharSet.dot_all() if node.matches_newline else CharSet.dot()
        return frag_char(self.alloc, cs)

    def _visit_charclass(self, node: CharClassNode) -> NFAFragment:
        cs = self._resolve_charclass(node)
        return frag_char(self.alloc, cs)

    def _visit_setclass(self, node: SetClassNode) -> NFAFragment:
        cs = CharSet()
        for item in node.items:
            if isinstance(item, LiteralNode):
                for ch in item.value:
                    cs = cs | CharSet.from_char(ch)
            elif isinstance(item, RangeNode):
                cs = cs | CharSet.from_range(item.start, item.end)
            elif isinstance(item, CharClassNode):
                cs = cs | self._resolve_charclass(item)

        if node.negated:
            cs = ~cs

        if not cs:
            return frag_epsilon(self.alloc)
        return frag_char(self.alloc, cs)

    def _visit_alternation(self, node: AlternationNode) -> NFAFragment:
        left = self._visit(node.left)
        right = self._visit(node.right)
        return frag_alternate(self.alloc, left, right)

    def _visit_group(self, node: GroupNode) -> NFAFragment:
        # Lookaheads/lookbehinds don't consume input in the NFA
        if node.type in (
            "lookahead",
            "negative_lookahead",
            "lookbehind",
            "negative_lookbehind",
        ):
            return frag_epsilon(self.alloc)

        if not node.children:
            return frag_epsilon(self.alloc)
        return self._concat_children(node.children)

    def _visit_quantifier(self, node: QuantifierNode) -> NFAFragment:
        # We need a factory so frag_repeat can build fresh copies
        def child_factory() -> NFAFragment:
            return self._visit(node.child)

        return frag_repeat(
            self.alloc,
            child_factory,
            min_n=node.min,
            max_n=node.max,
            greedy=node.greedy,
        )

    # ── Helpers ───────────────────────────────────────────────────

    def _concat_children(self, children: list[AstNode]) -> NFAFragment:
        result: NFAFragment | None = None
        for child in children:
            f = self._visit(child)
            result = frag_concat(result, f) if result else f
        return result or frag_epsilon(self.alloc)

    @staticmethod
    def _resolve_charclass(node: CharClassNode) -> CharSet:
        """Resolve \\d, \\w, \\s and their negations to CharSets."""
        base_map = {
            "digit": CharSet.digit,
            "word": CharSet.word,
            "whitespace": CharSet.whitespace,
        }
        factory = base_map.get(node.type)
        if factory:
            cs = factory()
            return ~cs if node.negated else cs
        # Unknown type — treat as dot
        return CharSet.dot()
