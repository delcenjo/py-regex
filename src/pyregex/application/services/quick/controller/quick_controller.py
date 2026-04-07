from __future__ import annotations
from typing import Any, Tuple, List
from pyregex.application.services.quick.pipeline.quick_pipeline import QuickPipeline
from pyregex.application.services.quick.knowledge.alias_registry import AliasRegistry


class QuickController:
    """The master controller for the QUICK sub-system."""

    def __init__(self, registry: Any):
        self.alias_registry = AliasRegistry()
        self.pipeline = QuickPipeline(registry, self.alias_registry)

    def process_intent(self, user_input: str) -> Tuple[Any, List[str]]:
        """
        Processes a natural language intent and returns a builder
        and associated tags.
        """
        state = self.pipeline.run(user_input)

        if state.selected_builder:
            tags = ["quick", "intent"]
            if state.confidence_score > 0.8:
                tags.append("high-confidence")
            return state.selected_builder, tags

        return None, []
