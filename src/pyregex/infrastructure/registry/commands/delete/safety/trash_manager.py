import json
from pathlib import Path
from datetime import datetime
from pyregex.infrastructure.registry.schema.models import RegistryPattern
from pyregex.infrastructure.registry.storage.json_backend import JsonStorageBackend


class TrashManager:
    """Handles mapping deleted items safely to a trash repository."""

    def __init__(self, trash_file_path: str | Path | None = None):
        if not trash_file_path:
            config_dir = Path.home() / ".pyregex"
            config_dir.mkdir(parents=True, exist_ok=True)
            trash_file_path = config_dir / "trash.json"

        self.trash_backend = JsonStorageBackend(Path(trash_file_path))

    def move_to_trash(self, pattern: RegistryPattern) -> None:
        """Saves the pattern to the trash backend with a timestamped name to avoid collisions."""
        pattern.metadata.updated_at = datetime.now().isoformat()

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        trashed_name = f"{pattern.name}__trashed_{timestamp}"

        from copy import deepcopy

        trashed_pattern = deepcopy(pattern)
        trashed_pattern.name = trashed_name
        self.trash_backend.save(trashed_pattern)

    def empty_trash(self) -> None:
        """Permanently wipes the trash."""
        if Path(self.trash_backend.file_path).exists():
            with open(self.trash_backend.file_path, "w") as f:
                json.dump({}, f)
