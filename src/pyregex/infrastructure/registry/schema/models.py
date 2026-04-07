from __future__ import annotations
from datetime import datetime
from typing import List, Any
from pydantic import BaseModel, Field


class PatternMetadata(BaseModel):
    """Rich metadata for a RegistryPattern."""

    description: str = Field(default="")
    tags: List[str] = Field(default_factory=list)
    category: str = Field(default="uncategorized")
    flags: List[str] = Field(default_factory=list)
    version: int = Field(default=1)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    usage_count: int = Field(default=0)
    origin: str = Field(default="manual")  # 'quick', 'create', 'manual', 'learn'

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PatternMetadata":
        return cls(
            description=data.get("description", ""),
            tags=data.get("tags", []),
            category=data.get("category", "uncategorized"),
            flags=data.get("flags", []),
            version=data.get("version", 1),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            usage_count=data.get("usage_count", 0),
            origin=data.get("origin", "manual"),
        )


class RegistryPattern(BaseModel):
    """Core domain model representing a saved regex asset in the Registry."""

    name: str
    pattern: str
    metadata: PatternMetadata = Field(default_factory=PatternMetadata)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegistryPattern":
        return cls(
            name=data["name"],
            pattern=data["pattern"],
            metadata=PatternMetadata.from_dict(data.get("metadata", {})),
        )
