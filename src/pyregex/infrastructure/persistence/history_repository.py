"""Repository for tracking recent regex pattern usage."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class HistoryEntry:
    """Represents an entry in the regex history."""

    pattern: str
    timestamp: str
    command: str  # e.g., 'test', 'explain', 'quick'

    def to_dict(self) -> dict:
        return asdict(self)


class HistoryRepository:
    """Manages a JSON-based history of recent patterns."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self._max_entries = 50

    def add(self, pattern: str, command: str) -> None:
        """Add a new entry to history."""
        history = self._load()

        # Avoid duplicate consecutive entries
        if history and history[0]["pattern"] == pattern:
            history[0]["timestamp"] = datetime.now().isoformat()
        else:
            entry = HistoryEntry(
                pattern=pattern, timestamp=datetime.now().isoformat(), command=command
            )
            history.insert(0, entry.to_dict())

        # Limit history size
        history = history[: self._max_entries]
        self._save(history)

    def list_recent(self, count: int = 10) -> list[dict]:
        """Return the most recent history entries."""
        return self._load()[:count]

    def clear(self) -> None:
        """Clear all history."""
        self._save([])

    def _load(self) -> list[dict]:
        """Load history from file."""
        if not self.storage_path.exists():
            return []
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            return list(data) if isinstance(data, list) else []
        except (json.JSONDecodeError, IOError):
            return []

    def _save(self, history: list[dict]) -> None:
        """Save history to file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(json.dumps(history, indent=2), encoding="utf-8")
