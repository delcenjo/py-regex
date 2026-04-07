import os
import yaml
from pathlib import Path
from typing import Optional, Any, Dict


class ProjectContext:
    """Manages project-level settings and custom pattern discovery.

    Looks for .pyregex.yaml in the current and parent directories.
    """

    def __init__(self, start_path: Optional[str] = None):
        self.root = self._find_project_root(start_path or os.getcwd())
        self.config_path = self.root / ".pyregex.yaml" if self.root else None
        self.config: Dict[str, Any] = {}
        self.load()

    def _find_project_root(self, current: str) -> Optional[Path]:
        curr = Path(current).resolve()
        for parent in [curr] + list(curr.parents):
            if (parent / ".pyregex.yaml").exists() or (parent / ".git").exists():
                return parent
        return None

    def load(self):
        """Loads configuration from .pyregex.yaml."""
        if self.config_path and self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f) or {}
                self._apply_config()
            except Exception:
                # Silently fail (or log) for dev tool
                pass

    def _apply_config(self):
        """Merges custom patterns from config into the global registry. (Deprecated)"""
        pass

    def save_pattern(self, name: str, pattern: str, tags: Optional[list] = None):
        """Saves a new pattern to the project configuration."""
        if not self.config_path:
            self.root = Path(os.getcwd())
            self.config_path = self.root / ".pyregex.yaml"

        if "patterns" not in self.config:
            self.config["patterns"] = {}

        self.config["patterns"][name] = {"pattern": pattern, "tags": tags or ["custom"]}

        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, sort_keys=False)
        except Exception:
            pass


# Singleton for the current session
current_context = ProjectContext()
