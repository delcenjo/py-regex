import json
from pathlib import Path
from typing import List, Optional, Any
from pyregex.infrastructure.registry.schema.models import (
    RegistryPattern,
    PatternMetadata,
)
from pyregex.infrastructure.registry.storage.backend import StorageBackend


class JsonStorageBackend(StorageBackend):
    """Storage implementation that uses the legacy patterns.json file for seamless upgrading."""

    def __init__(self, file_path: Optional[Path] = None):
        self.file_path = file_path or (Path.home() / ".pyregex" / "patterns.json")
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_data(self) -> List[dict[str, Any]]:
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _write_data(self, data: List[dict[str, Any]]) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    def _dict_to_model(self, data: dict[str, Any]) -> RegistryPattern:
        # Handle new format vs legacy format migration gracefully
        if "metadata" in data:
            return RegistryPattern.from_dict(data)

        # Migrate legacy mapping
        meta = PatternMetadata(
            description=data.get("description", ""),
            tags=data.get("tags", []),
            flags=data.get("flags", []),
            created_at=data.get("created_at", PatternMetadata().created_at),
        )
        return RegistryPattern(
            name=data["name"], pattern=data["pattern"], metadata=meta
        )

    def get_all(self) -> List[RegistryPattern]:
        raw_data = self._read_data()
        return [self._dict_to_model(item) for item in raw_data]

    def get(self, name: str) -> Optional[RegistryPattern]:
        for pattern in self.get_all():
            if pattern.name == name:
                return pattern
        return None

    def save(self, pattern: RegistryPattern) -> None:
        raw_data = self._read_data()
        updated = False

        for i, item in enumerate(raw_data):
            if item.get("name") == pattern.name:
                raw_data[i] = pattern.to_dict()
                updated = True
                break

        if not updated:
            raw_data.append(pattern.to_dict())

        self._write_data(raw_data)

    def delete(self, name: str) -> bool:
        raw_data = self._read_data()
        original_len = len(raw_data)
        filtered_data = [item for item in raw_data if item.get("name") != name]

        if len(filtered_data) < original_len:
            self._write_data(filtered_data)
            return True
        return False
