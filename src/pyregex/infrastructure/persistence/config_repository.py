"""Repository for managing application configuration."""

from __future__ import annotations

import json
from pathlib import Path

from pyregex.infrastructure.config.models import AppConfig


class ConfigRepository:
    """Handles persistence of AppConfig to ~/.pyregex/config.json."""

    @staticmethod
    def get_default_config_dir() -> Path:
        """Return the default configuration directory."""
        return Path.home() / ".pyregex"

    def __init__(self, config_dir: str | Path | None = None):
        if config_dir:
            self.config_path = Path(config_dir) / "config.json"
        else:
            self.config_path = self.get_default_config_dir() / "config.json"

        self.config_path.parent.mkdir(parents=True, exist_ok=True)

    def exists(self) -> bool:
        """Check if config file exists."""
        return self.config_path.exists()

    def load(self) -> AppConfig:
        """Load configuration from file."""
        if not self.exists():
            return AppConfig()

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppConfig.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return AppConfig()

    def save(self, config: AppConfig) -> None:
        """Save configuration to file."""
        from pyregex.utils.atomic import atomic_write

        atomic_write(self.config_path, json.dumps(config.to_dict(), indent=2))

    def get_path(self) -> str:
        """Return the absolute path to the config file."""
        return str(self.config_path.absolute())
