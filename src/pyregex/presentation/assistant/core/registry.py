"""Nebula Assistant Engine — Module Registry with Auto-Discovery."""

from __future__ import annotations
from typing import Any, Optional
from collections import OrderedDict

from pyregex.presentation.assistant.core.types import (
    ModuleInfo,
    ModuleCategory,
    ModuleProtocol,
    EventType,
)
from pyregex.presentation.assistant.core.events import EventBus
from pyregex.presentation.assistant.core.errors import ModuleError, ModuleNotFoundError


_REGISTERED_MODULE_CLASSES: list[type] = []


def register_module(cls: type) -> type:
    """Decorator that marks a class for auto-discovery by the ModuleRegistry."""
    _REGISTERED_MODULE_CLASSES.append(cls)
    return cls


class ModuleRegistry:
    """
    Central registry for all assistant modules.

    Supports:
    - Auto-discovery of @register_module decorated classes
    - Manual registration
    - Lookup by name or category
    - Dependency-aware loading order
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        self._modules: OrderedDict[str, ModuleProtocol] = OrderedDict()
        self._module_info: OrderedDict[str, ModuleInfo] = OrderedDict()
        self._by_category: dict[ModuleCategory, list[str]] = {}
        self._event_bus = event_bus

    def register(self, module: ModuleProtocol) -> None:
        """Register a module instance."""
        info = module.info
        if info.name in self._modules:
            raise ModuleError(f"Module already registered: {info.name}", info.name)

        self._modules[info.name] = module
        self._module_info[info.name] = info

        cat = info.category
        if cat not in self._by_category:
            self._by_category[cat] = []
        self._by_category[cat].append(info.name)

        if self._event_bus:
            self._event_bus.emit_simple(
                EventType.MODULE_ENTER,
                source="registry",
                module=info.name,
                category=cat.value,
            )

    def discover(self, cli: Any = None) -> int:
        """
        Auto-discover and register all @register_module decorated classes.
        Returns the number of modules discovered.
        """
        count = 0
        for cls in _REGISTERED_MODULE_CLASSES:
            try:
                instance = cls(cli) if cli else cls()
                if isinstance(instance, ModuleProtocol):
                    self.register(instance)
                    count += 1
            except Exception:
                continue
        return count

    def get(self, name: str) -> ModuleProtocol:
        """Get a module by name. Raises ModuleNotFoundError if not found."""
        if name not in self._modules:
            raise ModuleNotFoundError(name)
        return self._modules[name]

    def get_safe(self, name: str) -> Optional[ModuleProtocol]:
        """Get a module by name, returning None if not found."""
        return self._modules.get(name)

    def get_by_category(self, category: ModuleCategory) -> list[ModuleProtocol]:
        """Get all modules in a category."""
        names = self._by_category.get(category, [])
        return [self._modules[n] for n in names]

    def get_info(self, name: str) -> Optional[ModuleInfo]:
        """Get module metadata."""
        return self._module_info.get(name)

    def list_all(self) -> list[ModuleInfo]:
        """List all registered module info objects."""
        return list(self._module_info.values())

    def list_categories(self) -> list[ModuleCategory]:
        """List all categories that have modules registered."""
        return list(self._by_category.keys())

    def search(self, query: str) -> list[ModuleInfo]:
        """Search modules by name or description."""
        query = query.lower()
        if len(query) < 3:
            return []  # Prevent fuzzy matching single/double characters
            
        results = []
        for info in self._module_info.values():
            if (
                query in info.name.lower()
                or query in info.display_name.lower()
                or query in info.description.lower()
            ):
                results.append(info)
        return results

    @property
    def count(self) -> int:
        return len(self._modules)

    @property
    def names(self) -> list[str]:
        return list(self._modules.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._modules

    def __len__(self) -> int:
        return len(self._modules)
