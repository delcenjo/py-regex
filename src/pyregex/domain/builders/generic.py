"""Universal Regex Builder driven by catalog metadata.

This builder eliminates the need for individual generated builder classes
by interpreting YAML pattern and subtype logic at runtime.
"""

from __future__ import annotations
import re
from typing import Any, Pattern, Optional

from pyregex.domain.builders.base import RegexBuilder, BuilderMetadata
from pyregex.domain.catalog.registry import CatalogEntry


class GenericBuilder(RegexBuilder):
    """A generic builder that constructs regexes from a CatalogEntry."""

    def __init__(self, entry: CatalogEntry, config: Optional[dict[str, Any]] = None):
        self.entry = entry
        self.config = self.default_config()
        if config:
            self.config.update(config)

    @property
    def metadata(self) -> BuilderMetadata:
        all_examples = []
        all_non_examples = []
        
        for sub in self.entry.subtypes.values():
            all_examples.extend(sub.get("examples", []))
            all_non_examples.extend(sub.get("non_examples", []))
            
        return BuilderMetadata(
            name=self.entry.name,
            category=self.entry.category,
            description=self.entry.description,
            examples=all_examples,
            non_examples=all_non_examples
        )

    def default_config(self) -> dict[str, Any]:
        """Returns default config. Usually just uses the first subtype."""
        return {
            "subtype": self.entry.default_subtype
        }

    def build(self, config: dict[str, Any] | None = None) -> Pattern[str]:
        if config:
            self.config.update(config)
        return re.compile(self.build_pattern())

    def build_pattern(self) -> str:
        """Resolves the pattern based on the selected subtype."""
        subtype_name = self.config.get("subtype", self.entry.default_subtype)
        subtype_cfg = self.entry.subtypes.get(subtype_name)
        
        if not subtype_cfg:
            # Fallback to standard if subtype not found
            subtype_cfg = self.entry.subtypes.get("standard", next(iter(self.entry.subtypes.values())))
            
        pattern = subtype_cfg.get("pattern", "")
        
        # Try to format the pattern with the configuration values (e.g., {region})
        try:
            return pattern.format(**self.config)
        except (KeyError, IndexError, ValueError):
            return pattern

    def get_examples(self) -> list[str]:
        subtype_name = self.config.get("subtype", self.entry.default_subtype)
        subtype_cfg = self.entry.subtypes.get(subtype_name, {})
        return subtype_cfg.get("examples", [])

    def get_non_examples(self) -> list[str]:
        subtype_name = self.config.get("subtype", self.entry.default_subtype)
        subtype_cfg = self.entry.subtypes.get(subtype_name, {})
        return subtype_cfg.get("non_examples", [])
