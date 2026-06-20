from __future__ import annotations
from typing import List, Dict, Any, Optional
from pyregex.application.services.quick.base import QuickModule


class Scorer(QuickModule):
    """Scores candidate intents based on various heuristics."""

    def score(self, intents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for intent in intents:
            # Simple scoring: exact matches are better
            # (In a real system, we might use word frequency or past usage)
            intent["score"] = intent.get("confidence", 0.0)

            # Boost based on specificity
            if "strict" in intent:
                intent["score"] += 0.2

        return sorted(intents, key=lambda x: x["score"], reverse=True)


class Selector(QuickModule):
    """Selects the best interpretation from scored candidates."""

    def select(self, intents: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not intents:
            return None
        # Return the one with highest score
        return intents[0]
