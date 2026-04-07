from dataclasses import dataclass
from typing import Any
import os
from pathlib import Path

from pyregex.domain.interfaces.repositories import (
    PatternRepositoryPort,
    ConfigRepositoryPort,
    HistoryRepositoryPort,
)
from pyregex.infrastructure.persistence.config_repository import ConfigRepository
from pyregex.infrastructure.persistence.pattern_repository import PatternRepository
from pyregex.infrastructure.persistence.history_repository import HistoryRepository
from pyregex.domain.catalog.registry import CatalogRegistry

@dataclass
class AppContainer:
    """Simple Dependency Injection Container for PyRegex."""
    config: Any
    config_repo: ConfigRepositoryPort
    pattern_repo: PatternRepositoryPort
    history_repo: HistoryRepositoryPort
    catalog: CatalogRegistry

    @classmethod
    def create_default(cls, config: Any) -> "AppContainer":
        """Factory for production."""
        global_dir = Path(os.getenv("PYREGEX_GLOBAL_DIR", "/etc/pyregex"))
        config_repo = ConfigRepository()
        pattern_repo = PatternRepository(global_dir=global_dir)
        history_repo = HistoryRepository(
            ConfigRepository.get_default_config_dir() / "history.json"
        )
        catalog = CatalogRegistry()
        
        return cls(
            config=config,
            config_repo=config_repo,
            pattern_repo=pattern_repo,
            history_repo=history_repo,
            catalog=catalog,
        )
