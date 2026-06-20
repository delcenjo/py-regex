from __future__ import annotations
from typing import Any
from pyregex.application.services.quick.base import QuickState
from pyregex.application.services.quick.parsing.normalizer import Normalizer, Tokenizer
from pyregex.application.services.quick.resolution.intent_detector import (
    IntentDetector,
    EntityMapper,
)
from pyregex.application.services.quick.ranking.scorer import Scorer, Selector


class QuickPipeline:
    """Orchestrates the sequence of processing stages for QUICK."""

    def __init__(self, registry: Any, alias_registry: Any):
        self.normalizer = Normalizer()
        self.tokenizer = Tokenizer()
        self.intent_detector = IntentDetector(alias_registry)
        self.entity_mapper = EntityMapper(registry)
        self.scorer = Scorer()
        self.selector = Selector()

    def run(self, raw_input: str) -> QuickState:
        state = QuickState(raw_input)

        # 1. Parsing
        state.normalized_input = self.normalizer.normalize(state.raw_input)
        state.tokens = self.tokenizer.tokenize(state.normalized_input)

        # 2. Resolution
        state.intents = self.intent_detector.detect(state.tokens)

        # 3. Ranking
        scored_intents = self.scorer.score(state.intents)
        best_intent = self.selector.select(scored_intents)

        if best_intent:
            # 4. Building
            state.selected_builder = self.entity_mapper.resolve_builder(best_intent)
            state.confidence_score = best_intent.get("score", 0.0)

        return state
