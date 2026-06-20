"""NFA Fragment construction — Thompson's algorithm.

Converts individual AST nodes into NFA fragments that can be composed
via concatenation, alternation, and quantification.
"""

from __future__ import annotations
from pyregex.domain.explain.redos.models import (
    NFAState,
    NFAFragment,
    CharSet,
)


class StateAllocator:
    """Global state ID generator."""

    def __init__(self):
        self._counter = 0

    def new_state(self, **kwargs) -> NFAState:
        s = NFAState(id=self._counter, **kwargs)
        self._counter += 1
        return s

    @property
    def count(self) -> int:
        return self._counter


def frag_char(alloc: StateAllocator, charset: CharSet) -> NFAFragment:
    """Fragment that matches a single character from *charset*."""
    s = alloc.new_state()
    e = alloc.new_state()
    s.add_transition(e, charset)
    return NFAFragment(s, e)


def frag_epsilon(alloc: StateAllocator) -> NFAFragment:
    """Fragment that matches nothing (epsilon transition)."""
    s = alloc.new_state()
    e = alloc.new_state()
    s.add_transition(e)  # epsilon
    return NFAFragment(s, e)


def frag_concat(a: NFAFragment, b: NFAFragment) -> NFAFragment:
    """Concatenate two fragments: a then b."""
    a.end.add_transition(b.start)
    return NFAFragment(a.start, b.end)


def frag_alternate(
    alloc: StateAllocator, a: NFAFragment, b: NFAFragment
) -> NFAFragment:
    """Alternation: a | b."""
    s = alloc.new_state()
    e = alloc.new_state()
    s.add_transition(a.start)
    s.add_transition(b.start)
    a.end.add_transition(e)
    b.end.add_transition(e)
    return NFAFragment(s, e)


def frag_star(
    alloc: StateAllocator, child: NFAFragment, greedy: bool = True
) -> NFAFragment:
    """Quantifier: child* (zero or more)."""
    s = alloc.new_state()
    e = alloc.new_state()
    s.add_transition(child.start)
    s.add_transition(e)
    child.end.add_transition(child.start)
    child.end.add_transition(e)
    return NFAFragment(s, e)


def frag_plus(
    alloc: StateAllocator, child: NFAFragment, greedy: bool = True
) -> NFAFragment:
    """Quantifier: child+ (one or more)."""
    s = alloc.new_state()
    e = alloc.new_state()
    s.add_transition(child.start)
    child.end.add_transition(child.start)
    child.end.add_transition(e)
    return NFAFragment(s, e)


def frag_optional(
    alloc: StateAllocator, child: NFAFragment, greedy: bool = True
) -> NFAFragment:
    """Quantifier: child? (zero or one)."""
    s = alloc.new_state()
    e = alloc.new_state()
    s.add_transition(child.start)
    s.add_transition(e)
    child.end.add_transition(e)
    return NFAFragment(s, e)


def frag_repeat(
    alloc: StateAllocator,
    child_factory,
    min_n: int,
    max_n: int | None,
    greedy: bool = True,
) -> NFAFragment:
    """Quantifier: child{min,max}.

    *child_factory* is a callable that returns a fresh NFAFragment each time
    (needed because we can't reuse NFA states).
    """
    if min_n == 0 and max_n is None:
        return frag_star(alloc, child_factory(), greedy)
    if min_n == 1 and max_n is None:
        return frag_plus(alloc, child_factory(), greedy)
    if min_n == 0 and max_n == 1:
        return frag_optional(alloc, child_factory(), greedy)

    # Chain min mandatory copies
    result: NFAFragment | None = None
    for _ in range(min_n):
        f = child_factory()
        result = frag_concat(result, f) if result else f

    if max_n is None:
        # {min,} — min copies + star
        star = frag_star(alloc, child_factory(), greedy)
        result = frag_concat(result, star) if result else star
    elif max_n > min_n:
        # {min,max} — min copies + (max-min) optional copies
        for _ in range(max_n - min_n):
            opt = frag_optional(alloc, child_factory(), greedy)
            result = frag_concat(result, opt) if result else opt

    if result is None:
        return frag_epsilon(alloc)
    return result
