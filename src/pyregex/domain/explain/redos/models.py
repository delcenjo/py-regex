"""ReDoS Engine — Data Models.

Core data structures for NFA construction, vulnerability detection,
and analysis reporting.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CharSet:
    """Bitset over 256 ASCII codepoints for fast character set operations.

    Supports O(1) intersection, union, and membership queries via
    Python's arbitrary-precision int as a bitmask.
    """

    __slots__ = ("_bits",)

    def __init__(self, bits: int = 0):
        self._bits = bits

    @classmethod
    def from_char(cls, c: str) -> CharSet:
        return cls(1 << ord(c))

    @classmethod
    def from_range(cls, start: str, end: str) -> CharSet:
        lo, hi = ord(start), ord(end)
        if lo > hi:
            lo, hi = hi, lo
        bits = 0
        for i in range(lo, hi + 1):
            bits |= 1 << i
        return cls(bits)

    @classmethod
    def from_chars(cls, chars: str) -> CharSet:
        bits = 0
        for c in chars:
            bits |= 1 << ord(c)
        return cls(bits)

    @classmethod
    def dot(cls) -> CharSet:
        """Any character except newline."""
        bits = 0
        for i in range(256):
            if i != 10:  # exclude \n
                bits |= 1 << i
        return cls(bits)

    @classmethod
    def dot_all(cls) -> CharSet:
        """Any character including newline (DOTALL)."""
        return cls((1 << 256) - 1)

    @classmethod
    def word(cls) -> CharSet:
        """[a-zA-Z0-9_]"""
        cs = cls()
        cs = cs | cls.from_range("a", "z")
        cs = cs | cls.from_range("A", "Z")
        cs = cs | cls.from_range("0", "9")
        cs = cs | cls.from_char("_")
        return cs

    @classmethod
    def digit(cls) -> CharSet:
        """[0-9]"""
        return cls.from_range("0", "9")

    @classmethod
    def whitespace(cls) -> CharSet:
        """[ \\t\\n\\r\\f\\v]"""
        return cls.from_chars(" \t\n\r\f\v")

    def __contains__(self, c: str) -> bool:
        return bool(self._bits & (1 << ord(c)))

    def __or__(self, other: CharSet) -> CharSet:
        return CharSet(self._bits | other._bits)

    def __and__(self, other: CharSet) -> CharSet:
        return CharSet(self._bits & other._bits)

    def __invert__(self) -> CharSet:
        return CharSet(((1 << 256) - 1) ^ self._bits)

    def __bool__(self) -> bool:
        return self._bits != 0

    def __eq__(self, other: object) -> bool:
        return isinstance(other, CharSet) and self._bits == other._bits

    def __hash__(self) -> int:
        return hash(self._bits)

    def intersects(self, other: CharSet) -> bool:
        """O(1) intersection test."""
        return bool(self._bits & other._bits)

    def intersection(self, other: CharSet) -> CharSet:
        return self & other

    def union(self, other: CharSet) -> CharSet:
        return self | other

    def is_subset(self, other: CharSet) -> bool:
        return (self._bits & other._bits) == self._bits

    def count(self) -> int:
        """Number of characters in the set."""
        return bin(self._bits).count("1")

    def sample_char(self) -> Optional[str]:
        """Return any single character from the set (for pump generation)."""
        if not self._bits:
            return None
        # Find lowest set bit
        low = self._bits & (-self._bits)
        return chr(low.bit_length() - 1)

    def sample_outside(self) -> Optional[str]:
        """Return a character NOT in this set (for suffix generation)."""
        inv = ~self
        return inv.sample_char()

    def __repr__(self) -> str:
        n = self.count()
        if n == 0:
            return "CharSet(∅)"
        if n <= 10:
            chars = [chr(i) for i in range(256) if self._bits & (1 << i)]
            return "CharSet({''.join(repr(c) for c in chars)})"
        return f"CharSet({n} chars)"


class TransitionType(Enum):
    CHAR = "char"  # Transition on a CharSet
    EPSILON = "epsilon"  # Free transition


@dataclass
class NFATransition:
    """A single NFA transition edge."""

    target: NFAState
    type: TransitionType
    charset: Optional[CharSet] = None  # None for epsilon

    def accepts(self, c: str) -> bool:
        if self.type == TransitionType.EPSILON:
            return False
        return self.charset is not None and c in self.charset


@dataclass
class NFAState:
    """A single NFA state with outgoing transitions."""

    id: int
    transitions: list[NFATransition] = field(default_factory=list)
    is_accept: bool = False

    # Metadata for tracing back to AST
    ast_position: Optional[int] = None

    def add_transition(self, target: NFAState, charset: Optional[CharSet] = None):
        if charset is None:
            self.transitions.append(NFATransition(target, TransitionType.EPSILON))
        else:
            self.transitions.append(NFATransition(target, TransitionType.CHAR, charset))

    def char_transitions(self) -> list[NFATransition]:
        return [t for t in self.transitions if t.type == TransitionType.CHAR]

    def epsilon_transitions(self) -> list[NFATransition]:
        return [t for t in self.transitions if t.type == TransitionType.EPSILON]


@dataclass
class NFAFragment:
    """A fragment of an NFA with a start and end state.

    Used during Thompson construction — fragments are composed
    by concatenation, alternation, and quantification.
    """

    start: NFAState
    end: NFAState


class VulnType(Enum):
    NESTED_QUANTIFIER = "nested_quantifier"  # (a+)+
    ADJACENT_OVERLAP = "adjacent_overlap"  # \w+\w+
    ALTERNATION_OVERLAP = "alternation_overlap"  # (a|[a-z])+
    QUANTIFIER_SUFFIX_OVERLAP = "quantifier_suffix"  # [a-z]+a
    STAR_HEIGHT = "star_height"  # Deep nesting
    MULTIPLE_WILDCARDS = "multiple_wildcards"  # .*foo.*bar.*


class Severity(Enum):
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __ge__(self, other: Severity) -> bool:
        order = list(Severity)
        return order.index(self) >= order.index(other)

    def __gt__(self, other: Severity) -> bool:
        order = list(Severity)
        return order.index(self) > order.index(other)

    def __le__(self, other: Severity) -> bool:
        order = list(Severity)
        return order.index(self) <= order.index(other)

    def __lt__(self, other: Severity) -> bool:
        order = list(Severity)
        return order.index(self) < order.index(other)

    @classmethod
    def max(cls, a: Severity, b: Severity) -> Severity:
        return a if a >= b else b


@dataclass
class Vulnerability:
    """A single detected vulnerability in a regex pattern."""

    type: VulnType
    severity: Severity
    position: int = 0  # Character position in original pattern
    span: tuple[int, int] = (0, 0)  # Start-end range in pattern
    description: str = ""
    explanation: str = ""  # Technical detail
    fix_suggestion: str = ""  # Suggested safe alternative

    @property
    def icon(self) -> str:
        icons = {
            Severity.SAFE: "",
            Severity.LOW: "",
            Severity.MEDIUM: "",
            Severity.HIGH: "",
            Severity.CRITICAL: "",
        }
        return icons.get(self.severity, "")


@dataclass
class ComplexityResult:
    """Big-O complexity classification."""

    notation: str = "O(N)"  # O(N), O(N²), O(N³), O(2^N)
    numeric_score: int = 10  # 0-100 scale
    explanation: str = ""
    anchor_protected: bool = False


@dataclass
class ReDoSReport:
    """Complete ReDoS analysis report."""

    pattern: str = ""
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    complexity: ComplexityResult = field(default_factory=ComplexityResult)
    evil_input: Optional[str] = None
    pump_char: Optional[str] = None
    safe_rewrite: Optional[str] = None
    nfa_state_count: int = 0

    @property
    def risk_level(self) -> Severity:
        if not self.vulnerabilities:
            return Severity.SAFE
        return max(
            (v.severity for v in self.vulnerabilities),
            key=lambda s: list(Severity).index(s),
        )

    @property
    def is_vulnerable(self) -> bool:
        return self.risk_level >= Severity.HIGH

    @property
    def icon(self) -> str:
        icons = {
            Severity.SAFE: "",
            Severity.LOW: "",
            Severity.MEDIUM: "",
            Severity.HIGH: "",
            Severity.CRITICAL: "",
        }
        return icons.get(self.risk_level, "")

    def to_dict(self) -> dict:
        return {
            "pattern": self.pattern,
            "risk_level": self.risk_level.value,
            "is_vulnerable": self.is_vulnerable,
            "complexity": self.complexity.notation,
            "complexity_score": self.complexity.numeric_score,
            "vulnerabilities": [
                {
                    "type": v.type.value,
                    "severity": v.severity.value,
                    "position": v.position,
                    "description": v.description,
                    "fix": v.fix_suggestion,
                }
                for v in self.vulnerabilities
            ],
            "evil_input": self.evil_input,
            "safe_rewrite": self.safe_rewrite,
            "nfa_states": self.nfa_state_count,
        }
