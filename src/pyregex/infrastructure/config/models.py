"""Application configuration data models."""

from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Application configuration stored in ~/.pyregex/config.json."""

    language: str = Field(default="en")
    region: str = Field(default="US")
    theme: str = Field(default="dark")
    show_examples: bool = Field(default=True)
    default_date_format: str = Field(default="EU")
    default_date_separator: str = Field(default="/")
    debug: bool = Field(default=False)
    export_dir: str = Field(default="~/pyregex_exports")

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        return cls(**data)

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
        else:
            return False
        return True
