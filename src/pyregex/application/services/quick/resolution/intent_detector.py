from __future__ import annotations
from typing import List, Dict, Any, Optional
from pyregex.application.services.quick.base import QuickModule
from pyregex.application.services.quick.knowledge.alias_registry import AliasRegistry


class IntentDetector(QuickModule):
    """Identifies the underlying intent of the user input."""

    def __init__(self, alias_registry: AliasRegistry):
        super().__init__()
        self.alias_registry = alias_registry

    def detect(self, tokens: List[str]) -> List[Dict[str, Any]]:
        intents = []
        for token in tokens:
            pattern_id = self.alias_registry.get_pattern_by_alias(token)
            if pattern_id:
                intents.append(
                    {
                        "type": "BUILD",
                        "pattern_id": pattern_id,
                        "confidence": 0.5,  # Initial base confidence
                    }
                )

        # Modifier detection (e.g., 'strict', 'loose')
        if "strict" in tokens:
            for intent in intents:
                intent["strict"] = True
                intent["confidence"] = float(intent["confidence"]) + 0.1

        return intents


class EntityMapper(QuickModule):
    """Maps intent data to actual RegexBuilder instances."""

    def resolve_builder(self, intent: Dict[str, Any]) -> Optional[Any]:
        from pyregex.domain.catalog.registry import catalog_registry
        from pyregex.domain.builders.generic import GenericBuilder

        pid = intent.get("pattern_id")
        if pid:
            entry = catalog_registry.get_entry(pid)
            if entry:
                return GenericBuilder(entry)
        return None
