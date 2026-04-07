from abc import ABC, abstractmethod
from typing import List, Optional
from pyregex.infrastructure.registry.schema.models import RegistryPattern


class StorageBackend(ABC):
    """Abstract interface for Registry pattern storage."""

    @abstractmethod
    def save(self, pattern: RegistryPattern) -> None:
        pass

    @abstractmethod
    def get(self, name: str) -> Optional[RegistryPattern]:
        pass

    @abstractmethod
    def get_all(self) -> List[RegistryPattern]:
        pass

    @abstractmethod
    def delete(self, name: str) -> bool:
        pass
