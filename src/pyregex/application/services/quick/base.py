from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class QuickModule(ABC):
    """Base class for all modules in the QUICK sub-system."""

    def __init__(self, context: Optional[QuickContext] = None):
        self.context = context


class PipelineStage(ABC):
    """Base class for a stage in the QuickPipeline."""

    @abstractmethod
    def execute(self, state: QuickState) -> QuickState:
        pass


class QuickState:
    """Carries the state through the QuickPipeline."""

    def __init__(self, raw_input: str):
        self.raw_input = raw_input
        self.tokens: List[str] = []
        self.normalized_input: str = ""
        self.intents: List[Dict[str, Any]] = []
        self.entities: List[Dict[str, Any]] = []
        self.selected_builder: Optional[Any] = None
        self.confidence_score: float = 0.0
        self.alternative_builders: List[Any] = []
        self.metadata: Dict[str, Any] = {}


class QuickContext:
    """Shared context for the QUICK sub-system (session, history)."""

    def __init__(self):
        self.history: List[str] = []
        self.preferences: Dict[str, Any] = {}
