"""Dynamic Module that bridges the CatalogRegistry to the Assistant Engine."""

from __future__ import annotations
from typing import Any, Dict, Callable, Optional

from pyregex.presentation.assistant.core.types import ModuleInfo, ModuleCategory
from pyregex.domain.catalog.registry import catalog_registry, CatalogEntry
from pyregex.presentation.assistant.wizards.dynamic import DynamicWizard


class CatalogWizardAdapter:
    """Adapts a CatalogEntry to the AssistantEngine's wizard instantiation pattern."""

    def __init__(self, entry: CatalogEntry):
        self.entry = entry
        self.display_name = entry.wizard.get("display_name", entry.name.replace("_", " ").title())
        self.description = entry.description

    def __call__(self, cli: Any, session: Any = None) -> DynamicWizard:
        """Instantiate the dynamic wizard with the injected CLI."""
        return DynamicWizard(self.entry, cli)


class CatalogModule:
    """A dynamic module that exposes all catalog entries for a specific category."""

    def __init__(self, name: str, display_name: Optional[str] = None, icon: str = "🧩", description: str = "", cli: Any = None):
        # Enum safety: Find the category or use UTILS
        cat = ModuleCategory.UTILS
        for c in ModuleCategory:
            if c.value == name:
                cat = c
                break
        
        self._info = ModuleInfo(
            name=name,
            category=cat,
            display_name=display_name or name.replace("_", " ").title(),
            description=description,
            icon=icon
        )
        self.cli = cli

    @property
    def info(self) -> ModuleInfo:
        return self._info

    def get_wizards(self) -> Dict[str, Any]:
        """Returns a dict of wizard_name -> Adapter mapping for the category."""
        category_name = self._info.name
        entries = catalog_registry.list_entries(category_name)
        
        wizards = {}
        for entry_name in entries:
            entry = catalog_registry.get_entry(entry_name)
            if entry:
                # We use the raw entry name as the key, and append _wizard only if needed internally.
                # Actually, the Assistant expects wizard keys.
                # Let's use the entry_name directly as it is unique within the module.
                wizards[entry_name] = CatalogWizardAdapter(entry)
                
        return wizards

    def get_commands(self) -> Dict[str, Callable]:
        """Catalog modules don't have secondary commands yet."""
        return {}
