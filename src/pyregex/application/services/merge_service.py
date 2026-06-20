"""Service for merging and combining multiple regex patterns."""

from __future__ import annotations
import re
from typing import Dict, List


class RegexMergeService:
    """Handles the architectural combination of multiple regex patterns."""

    def merge(
        self, patterns: List[str], method: str = "or", grouping: str = "noncapture"
    ) -> str:
        """Combine multiple patterns using the specified method and grouping."""
        if not patterns:
            return ""

        if method == "trie":
            return self.trie_merge(patterns)

        processed_patterns = []
        for p in patterns:
            if grouping == "capture":
                processed_patterns.append(f"({p})")
            elif grouping == "noncapture":
                processed_patterns.append(f"(?:{p})")
            else:
                processed_patterns.append(p)

        if method == "or":
            return "|".join(processed_patterns)
        elif method == "concat":
            return "".join(processed_patterns)
        elif method == "optional":
            return "".join([f"(?:{p})?" for p in patterns])

        return "|".join(processed_patterns)

    def trie_merge(self, words: List[str]) -> str:
        """Build an optimized regex from a list of words using a Trie."""
        if not words:
            return ""

        trie = {}
        for word in words:
            curr = trie
            for char in word:
                if char not in curr:
                    curr[char] = {}
                curr = curr[char]
            curr[""] = True  # End of word

        return self._trie_to_regex(trie)

    def _trie_to_regex(self, trie: Dict) -> str:
        """Recursively convert a Trie dictionary to a regex string."""
        if not trie:
            return ""

        if len(trie) == 1 and "" in trie:
            return ""

        parts = []
        has_end = "" in trie

        # Sort keys to keep regex deterministic
        keys = sorted([k for k in trie.keys() if k != ""])

        # Group keys by their sub-trie to find commonalities
        for char in keys:
            sub_regex = self._trie_to_regex(trie[char])
            if sub_regex:
                parts.append(re.escape(char) + sub_regex)
            else:
                parts.append(re.escape(char))

        if len(parts) == 0:
            return ""

        # Combine parts: if multiple single chars, use a class [abc]
        single_chars = [p for p in parts if len(p) == 1]
        complex_parts = [p for p in parts if len(p) > 1]

        final_parts = []
        if len(single_chars) > 1:
            final_parts.append(f"[{''.join(single_chars)}]")
        elif len(single_chars) == 1:
            final_parts.append(single_chars[0])

        final_parts.extend(complex_parts)

        result = "|".join(final_parts)
        if len(final_parts) > 1:
            result = f"(?:{result})"

        if has_end:
            result = f"{result}?"

        return result

    def wrap_with_named_groups(self, patterns: List[tuple[str, str]]) -> str:
        """Combine patterns where each pattern is wrapped in a named group.
        Expects list of (name, pattern) tuples.
        """
        parts = []
        for name, pattern in patterns:
            clean_name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
            parts.append(f"(?P<{clean_name}>{pattern})")
        return "|".join(parts)

    def optimize_merged(self, pattern: str) -> str:
        """Analyze and optimize a large merged pattern."""
        if "|" not in pattern:
            return pattern

        # Basic: remove duplicate alternations
        parts = pattern.split("|")
        seen = set()
        unique_parts = []
        for p in parts:
            if p not in seen:
                unique_parts.append(p)
                seen.add(p)

        optimized = "|".join(unique_parts)

        # Advanced: check for nested ORs that can be flattened
        optimized = re.sub(r"\|\(:(.*?)\)\|", r"|\1|", optimized)

        return optimized
