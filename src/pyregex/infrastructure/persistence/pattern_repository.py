"""Repository for managing saved regex patterns."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
import logging

from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class SavedPattern:
    """Data model for a saved regex pattern."""

    name: str
    pattern: str
    flags: list[str] = field(default_factory=list)
    description: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_run: str | None = None
    scope: str = "private"  # 'private' or 'global'
    usage_count: int = 0
    is_favorite: bool = False
    is_pinned: bool = False
    collections: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SavedPattern":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


class PatternRepository:
    """Handles persistence of SavedPatterns to private and global storage."""

    def __init__(self, private_dir: Path | None = None, global_dir: Path | None = None):
        if private_dir:
            self.private_path = private_dir / "patterns.json"
        else:
            self.private_path = Path.home() / ".pyregex" / "patterns.json"

        if global_dir:
            self.global_path = global_dir / "patterns.json"
        else:
            # Default global path could be in /etc/pyregex or similar,
            # but for now we'll check if a specific ENV exists or just use a local one for development
            self.global_path = Path("/etc/pyregex/patterns.json")

        self.private_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_data(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save_data(self, data: list[dict[str, Any]], path: Path) -> None:
        try:
            from pyregex.utils.atomic import atomic_write

            atomic_write(path, json.dumps(data, indent=2))
        except OSError as e:
            logger.warning("Failed to save data to %s: %s", path, e)

    def list_all(
        self, tag: str | None = None, scope: str | None = None
    ) -> list[SavedPattern]:
        """List patterns, optionally filtered by tag or scope."""
        results = []

        if scope in (None, "global"):
            global_data = self._load_data(self.global_path)
            for item in global_data:
                p = SavedPattern.from_dict(item)
                p.scope = "global"
                results.append(p)

        if scope in (None, "private"):
            private_data = self._load_data(self.private_path)
            for item in private_data:
                p = SavedPattern.from_dict(item)
                p.scope = "private"
                results.append(p)

        if tag:
            tag = tag.lower()
            results = [p for p in results if tag in [t.lower() for t in p.tags]]

        return results

    def get(self, name: str) -> SavedPattern | None:
        """Get a pattern by name (searches private then global)."""
        private_data = self._load_data(self.private_path)
        for item in private_data:
            if item["name"] == name:
                p = SavedPattern.from_dict(item)
                p.scope = "private"
                return p

        global_data = self._load_data(self.global_path)
        for item in global_data:
            if item["name"] == name:
                p = SavedPattern.from_dict(item)
                p.scope = "global"
                return p

        return None

    def save(self, pattern: SavedPattern) -> None:
        """Save a pattern to private storage."""
        data = self._load_data(self.private_path)
        updated = False
        pattern.scope = "private"

        for i, item in enumerate(data):
            if item["name"] == pattern.name:
                data[i] = pattern.to_dict()
                updated = True
                break

        if not updated:
            data.append(pattern.to_dict())

        self._save_data(data, self.private_path)

    def delete(self, name: str) -> bool:
        """Delete from private storage."""
        data = self._load_data(self.private_path)
        initial_len = len(data)
        data = [item for item in data if item["name"] != name]
        if len(data) < initial_len:
            self._save_data(data, self.private_path)
            return True
        return False

    def update_last_run(self, name: str) -> None:
        """Update last_run and increment usage count for private patterns."""
        pattern = self.get(name)
        if pattern and pattern.scope == "private":
            pattern.last_run = datetime.now().isoformat()
            pattern.usage_count += 1
            self.save(pattern)

    def toggle_favorite(self, name: str) -> bool:
        pattern = self.get(name)
        if pattern and pattern.scope == "private":
            pattern.is_favorite = not pattern.is_favorite
            self.save(pattern)
            return pattern.is_favorite
        return False

    def toggle_pin(self, name: str) -> bool:
        pattern = self.get(name)
        if pattern and pattern.scope == "private":
            pattern.is_pinned = not pattern.is_pinned
            self.save(pattern)
            return pattern.is_pinned
        return False

    def add_to_collection(self, name: str, collection: str) -> bool:
        pattern = self.get(name)
        if pattern and pattern.scope == "private":
            if collection not in pattern.collections:
                pattern.collections.append(collection)
                self.save(pattern)
                return True
        return False

    def remove_from_collection(self, name: str, collection: str) -> bool:
        pattern = self.get(name)
        if pattern and pattern.scope == "private":
            if collection in pattern.collections:
                pattern.collections.remove(collection)
                self.save(pattern)
                return True
        return False

    def get_stats(self) -> dict[str, Any]:
        patterns = self.list_all(scope="private")
        return {
            "total": len(patterns),
            "favorites": len([p for p in patterns if p.is_favorite]),
            "pinned": len([p for p in patterns if p.is_pinned]),
            "most_used": sorted(patterns, key=lambda p: p.usage_count, reverse=True)[
                :5
            ],
            "collections": list(set([c for p in patterns for c in p.collections])),
        }
