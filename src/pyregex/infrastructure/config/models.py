"""Application configuration data models."""

from __future__ import annotations
from typing import Any
from dataclasses import dataclass, asdict


@dataclass
class AppConfig:
    """Application configuration stored in ~/.pyregex/config.json."""

    language: str = "en"
    region: str = "US"
    theme: str = "dark"
    show_examples: bool = True
    default_date_format: str = "EU"
    default_date_separator: str = "/"
    debug: bool = False
    export_dir: str = "~/pyregex_exports"
    show_toolbar: bool = True
    show_banner: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def set_value(self, key: str, value: str) -> bool:
        """Set a config value by key string. Returns True if successful."""
        if key == "language":
            if value not in ("en", "es"):
                return False
            self.language = value
        elif key == "region":
            self.region = value.upper()
        elif key == "theme":
            if value not in ("dark", "light"):
                return False
            self.theme = value
        elif key == "show_examples":
            self.show_examples = value.lower() in ("true", "yes", "1", "sí", "si")
        elif key == "default_date_format":
            if value.upper() not in ("EU", "US", "ISO"):
                return False
            self.default_date_format = value.upper()
        elif key == "default_date_separator":
            self.default_date_separator = value
        elif key == "debug":
            self.debug = value.lower() in ("true", "yes", "1", "sí", "si")
        elif key == "export_dir":
            self.export_dir = value
        elif key == "show_toolbar":
            self.show_toolbar = value.lower() in ("true", "yes", "1", "sí", "si")
        elif key == "show_banner":
            self.show_banner = value.lower() in ("true", "yes", "1", "sí", "si")
        else:
            return False
        return True
