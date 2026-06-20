import json
from pathlib import Path
from typing import List, Set


class TaskManager:
    """Manages persistent state for long-running batch operations.

    Saves progress to ~/.pyregex/tasks/<task_id>.json to allow resume capability.
    """

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.config_dir = Path.home() / ".pyregex" / "tasks"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.config_dir / f"{task_id}.json"
        self.completed_files: Set[str] = set()
        self.total_files: List[str] = []
        self._load()

    def _load(self):
        """Loads existing state if it exists."""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    data = json.load(f)
                    self.completed_files = set(data.get("completed", []))
                    self.total_files = data.get("total", [])
            except Exception:
                # If corrupted, start fresh
                pass

    def save(self):
        """Persists current state to disk."""
        with open(self.state_file, "w") as f:
            json.dump(
                {"completed": list(self.completed_files), "total": self.total_files},
                f,
                indent=2,
            )

    def initialize(self, files: List[str]):
        """Sets the pool of files if not already set (or if forcing reset)."""
        if not self.total_files:
            self.total_files = files
            self.save()

    def mark_complete(self, filepath: str):
        """Marks a file as finished and saves progress."""
        self.completed_files.add(filepath)
        self.save()

    def get_pending(self) -> List[str]:
        """Returns the list of files that still need processing."""
        return [f for f in self.total_files if f not in self.completed_files]

    def cleanup(self):
        """Removes the task file once 100% complete."""
        if self.state_file.exists():
            self.state_file.unlink()

    @property
    def progress(self) -> float:
        """Returns percentage completion."""
        if not self.total_files:
            return 0.0
        return (len(self.completed_files) / len(self.total_files)) * 100
