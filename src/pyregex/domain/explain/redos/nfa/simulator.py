"""NFA Simulator — Ambiguity detection and pump path tracing.

Walks the NFA graph to find states where the regex engine can enter
two different computation paths for the same input character.
These are the root cause of catastrophic backtracking.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from pyregex.domain.explain.redos.models import (
    NFAState,
    NFATransition,
    CharSet,
)


@dataclass
class AmbiguityPoint:
    """A point in the NFA where two paths accept overlapping characters."""

    state_id: int
    transition_a: NFATransition
    transition_b: NFATransition
    overlap: CharSet
    in_loop: bool = False  # True if this state is reachable from itself
    loop_depth: int = 0  # How many nested loops above this point

    @property
    def pump_char(self) -> Optional[str]:
        return self.overlap.sample_char()


@dataclass
class PumpPath:
    """A path through the NFA that can be 'pumped' to cause backtracking."""

    prefix: str = ""  # String to reach the ambiguous state
    pump: str = ""  # String that causes the exponential branching
    suffix: str = ""  # Non-matching suffix to force backtracking
    loop_count: int = 0  # How many times pump must repeat to see effect

    def generate_evil(self, pump_len: int = 25) -> str:
        return self.prefix + (self.pump * pump_len) + self.suffix


class NFASimulator:
    """Simulates NFA execution to find ambiguous paths.

    This is the core ReDoS detector. It performs:
    1. Epsilon closure computation
    2. Ambiguity detection (overlapping char transitions from same closure)
    3. Loop detection (states reachable from themselves)
    4. Pump path construction
    """

    def __init__(self, start: NFAState, accept: NFAState, max_states: int = 5000):
        self.start = start
        self.accept = accept
        self.max_states = max_states

    def find_ambiguities(self) -> list[AmbiguityPoint]:
        """Find all ambiguous points in the NFA."""
        ambiguities: list[AmbiguityPoint] = []
        visited: set[int] = set()
        loops = self._detect_loops()

        self._find_ambiguities_dfs(
            self.start, visited, ambiguities, loops, loop_depth=0
        )
        return ambiguities

    def trace_pump(self, ambiguity: AmbiguityPoint) -> PumpPath:
        """Given an ambiguity point, construct a pump path."""
        pump_char = ambiguity.pump_char
        if not pump_char:
            return PumpPath()

        # Find prefix: shortest string from start to ambiguous state
        prefix = self._shortest_path_to(ambiguity.state_id)

        # Find suffix: a character that does NOT match ANY transition
        # from the ambiguous state (to force full backtracking)
        suffix_char = self._find_failing_suffix(ambiguity.state_id)

        return PumpPath(
            prefix=prefix,
            pump=pump_char,
            suffix=suffix_char,
            loop_count=1 if ambiguity.in_loop else 0,
        )

    def classify_ambiguity(self, ambiguities: list[AmbiguityPoint]) -> str:
        """Classify overall complexity from ambiguity list.

        Returns: "O(N)", "O(N²)", "O(N³)", or "O(2^N)"
        """
        if not ambiguities:
            return "O(N)"

        max_loop_depth = max(a.loop_depth for a in ambiguities)
        has_nested = any(a.loop_depth >= 2 for a in ambiguities)
        has_loop_ambiguity = any(a.in_loop for a in ambiguities)

        if has_nested:
            return "O(2^N)"  # Nested quantifiers → exponential
        if has_loop_ambiguity:
            # Count how many independent loop-ambiguities
            loop_ambs = sum(1 for a in ambiguities if a.in_loop)
            if loop_ambs >= 3:
                return "O(N³)"
            if loop_ambs >= 2:
                return "O(N³)"
            return "O(N²)"
        return "O(N)"

    def _epsilon_closure(self, states: set[int]) -> set[int]:
        """Compute epsilon closure: all states reachable via epsilon transitions."""
        stack = list(states)
        closure = set(states)
        visited_count = 0

        while stack and visited_count < self.max_states:
            sid = stack.pop()
            state = self._get_state(sid)
            if state is None:
                continue
            for t in state.epsilon_transitions():
                if t.target.id not in closure:
                    closure.add(t.target.id)
                    stack.append(t.target.id)
            visited_count += 1

        return closure

    def _find_ambiguities_dfs(
        self,
        state: NFAState,
        visited: set[int],
        results: list[AmbiguityPoint],
        loops: set[int],
        loop_depth: int,
    ):
        """DFS through NFA looking for states with overlapping char transitions."""
        if state.id in visited or len(visited) > self.max_states:
            return
        visited.add(state.id)

        closure = self._epsilon_closure({state.id})

        char_trans: list[
            tuple[NFATransition, int]
        ] = []  # (transition, source_state_id)
        for sid in closure:
            s = self._get_state(sid)
            if s is None:
                continue
            for t in s.char_transitions():
                char_trans.append((t, sid))

        for i in range(len(char_trans)):
            for j in range(i + 1, len(char_trans)):
                t_a, sid_a = char_trans[i]
                t_b, sid_b = char_trans[j]

                if (
                    t_a.charset is not None
                    and t_b.charset is not None
                    and t_a.charset.intersects(t_b.charset)
                ):
                    if t_a.target.id != t_b.target.id:
                        in_loop = state.id in loops
                        results.append(
                            AmbiguityPoint(
                                state_id=state.id,
                                transition_a=t_a,
                                transition_b=t_b,
                                overlap=t_a.charset & t_b.charset,
                                in_loop=in_loop,
                                loop_depth=loop_depth + (1 if in_loop else 0),
                            )
                        )

        for t in state.transitions:
            child_depth = loop_depth + (1 if state.id in loops else 0)
            self._find_ambiguities_dfs(t.target, visited, results, loops, child_depth)

    def _detect_loops(self) -> set[int]:
        """Find all states that can reach themselves (loop states)."""
        loop_states: set[int] = set()
        all_states = self._collect_all_states()

        for state in all_states:
            if self._can_reach(state.id, state.id, set()):
                loop_states.add(state.id)

        return loop_states

    def _can_reach(
        self, from_id: int, target_id: int, visited: set[int], first: bool = True
    ) -> bool:
        """Check if from_id can reach target_id via any transitions."""
        if not first and from_id == target_id:
            return True
        if from_id in visited:
            return False
        visited.add(from_id)

        state = self._get_state(from_id)
        if state is None or len(visited) > self.max_states:
            return False

        for t in state.transitions:
            if self._can_reach(t.target.id, target_id, visited, first=False):
                return True
        return False

    def _shortest_path_to(self, target_id: int) -> str:
        """BFS to find shortest consuming string from start to target."""
        from collections import deque

        queue: deque[tuple[int, str, set[int]]] = deque()

        start_closure = self._epsilon_closure({self.start.id})
        for sid in start_closure:
            queue.append((sid, "", set()))

        while queue:
            current_id, path, visited = queue.popleft()

            if current_id == target_id:
                return path
            if current_id in visited or len(path) > 20:
                continue
            visited = visited | {current_id}

            state = self._get_state(current_id)
            if state is None:
                continue

            for t in state.epsilon_transitions():
                if t.target.id not in visited:
                    queue.append((t.target.id, path, visited))

            for t in state.char_transitions():
                if t.charset is not None:
                    sample = t.charset.sample_char()
                    if sample:
                        queue.append((t.target.id, path + sample, visited))

        return ""

    def _find_failing_suffix(self, state_id: int) -> str:
        """Find a character that transitions from state_id lead to rejection."""
        closure = self._epsilon_closure({state_id})
        accepted = CharSet()
        for sid in closure:
            s = self._get_state(sid)
            if s is None:
                continue
            for t in s.char_transitions():
                if t.charset is not None:
                    accepted = accepted | t.charset

        c = accepted.sample_outside()
        return c or "!"

    def _collect_all_states(self) -> list[NFAState]:
        """Collect all reachable states via BFS."""
        visited: set[int] = set()
        result: list[NFAState] = []
        stack = [self.start]

        while stack and len(visited) < self.max_states:
            s = stack.pop()
            if s.id in visited:
                continue
            visited.add(s.id)
            result.append(s)
            for t in s.transitions:
                if t.target.id not in visited:
                    stack.append(t.target)

        return result

    def _get_state(self, state_id: int) -> Optional[NFAState]:
        """Get state by ID via BFS (cached after first full scan)."""
        if not hasattr(self, "_state_map"):
            self._state_map: dict[int, NFAState] = {}
            for s in self._collect_all_states():
                self._state_map[s.id] = s

        return self._state_map.get(state_id)
