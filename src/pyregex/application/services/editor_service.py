import re
from typing import Optional, List, Dict, Any


class HistoryManager:
    """Manages undo/redo history for regex patterns with metadata."""

    def __init__(self, initial_pattern: str, initial_flags: str = ""):
        self.history: List[Dict[str, Any]] = [
            {
                "pattern": initial_pattern,
                "flags": initial_flags,
                "msg": "Initial pattern",
            }
        ]
        self.index: int = 0

    def add(self, pattern: str, flags: str, msg: str = "Applied change"):
        # Remove any forward history if we were in undo state
        while len(self.history) > self.index + 1:
            self.history.pop()
        self.history.append({"pattern": pattern, "flags": flags, "msg": msg})
        self.index += 1

    def undo(self) -> Optional[Dict[str, Any]]:
        if self.index > 0:
            self.index -= 1
            return self.history[self.index]
        return None

    def redo(self) -> Optional[Dict[str, Any]]:
        if self.index < len(self.history) - 1:
            self.index += 1
            return self.history[self.index]
        return None

    def get_current(self) -> Dict[str, Any]:
        return self.history[self.index]


class RegexEditorService:
    """Advanced logic for transforming and refactoring regex patterns."""

    @staticmethod
    def add_anchors(pattern: str, start: bool = True, end: bool = True) -> str:
        new_pattern = pattern
        if start and not new_pattern.startswith("^"):
            new_pattern = "^" + new_pattern
        if end and not new_pattern.endswith("$"):
            new_pattern = new_pattern + "$"
        return new_pattern

    @staticmethod
    def remove_anchors(pattern: str) -> str:
        new_pattern = pattern
        if new_pattern.startswith("^"):
            new_pattern = new_pattern.removeprefix("^")
        if new_pattern.endswith("$"):
            new_pattern = new_pattern.removesuffix("$")
        return new_pattern

    @staticmethod
    def rename_group(pattern: str, old_name: str, new_name: str) -> str:
        """Rename a named capturing group (?P<old_name>...) to (?P<new_name>...)."""
        # Rename the definition
        pattern = pattern.replace(f"(?P<{old_name}>", f"(?P<{new_name}>")
        # Rename backreferences (?P=old_name)
        pattern = pattern.replace(f"(?P={old_name})", f"(?P={new_name})")
        return pattern

    @staticmethod
    def wrap_in_group(
        pattern: str, group_type: str = "capture", name: Optional[str] = None
    ) -> str:
        if group_type == "capture":
            return f"({pattern})"
        elif group_type == "non_capture":
            return f"(?:{pattern})"
        elif group_type == "named" and name:
            return f"(?P<{name}>{pattern})"
        elif group_type == "optional":
            return f"(?:{pattern})?"
        return pattern

    @staticmethod
    def sanitize(pattern: str) -> str:
        """Remove redundant whitespace and empty groups."""
        # 1. Remove empty groups ()
        pattern = pattern.replace("()", "")
        # 2. Simplify nested redundant non-capturing groups (?:(?:a)) -> (?:a)
        pattern = re.sub(r"\(\?:\(\?:\s*(.*?)\s*\)\)", r"(?:\1)", pattern)
        return pattern

    @staticmethod
    def toggle_flag(flags: str, flag: str) -> str:
        if flag in flags:
            return flags.replace(flag, "")
        return "".join(sorted(flags + flag))

    @staticmethod
    def explain_change(old_pattern: str, new_pattern: str) -> str:
        """Generate a human-readable explanation of the difference."""
        if old_pattern == new_pattern:
            return "No change."
        if new_pattern == "^" + old_pattern + "$":
            return "Anchored to start and end."
        if new_pattern == "(?:" + old_pattern + ")":
            return "Wrapped in non-capturing group."
        return "Custom transformation applied."
