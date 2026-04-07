"""Dynamic Module that bridges the CatalogRegistry to the Assistant Engine."""

from __future__ import annotations
from typing import Any, Dict, Callable, Optional

from pyregex.presentation.assistant.core.types import ModuleInfo, ModuleCategory
from pyregex.domain.catalog.registry import catalog_registry, CatalogEntry
from pyregex.presentation.assistant.wizards.dynamic import DynamicWizard


class CatalogWizardAdapter:
    """Adapts a CatalogEntry to the AssistantEngine's wizard instantiation pattern."""

    def __init__(self, entry_or_name: CatalogEntry | str):
        if isinstance(entry_or_name, str):
            self.entry_name = entry_or_name
            self._entry = None
            # Fast heuristic for display name without loading YAML
            self.display_name = entry_or_name.replace("_", " ").title()
            self.description = "Wizard del catálogo de Nebula"
        else:
            self.entry_name = entry_or_name.name
            self._entry = entry_or_name
            self.display_name = entry_or_name.wizard.get("display_name", self.entry_name.replace("_", " ").title())
            self.description = entry_or_name.description

    def __call__(self, cli: Any, session: Any = None) -> DynamicWizard:
        """Instantiate the dynamic wizard with the injected CLI (Loads YAML on demand)."""
        if not self._entry:
            # ONLY Load YAML here, when the user actually runs the wizard
            self._entry = catalog_registry.get_entry(self.entry_name)
            
        return DynamicWizard(self._entry, cli)


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

    @property
    def wizard_count(self) -> int:
        """Efficiently returns the count of wizards without instantiating them."""
        return len(catalog_registry.list_entries(self._info.name))

    def get_wizards(self) -> Dict[str, Any]:
        """Returns a dict of wizard_name -> Adapter mapping for the category (Lazy)."""
        category_name = self._info.name
        # We only list the names. We DO NOT call get_entry() here.
        # This avoids opening thousands of YAML files.
        entry_names = catalog_registry.list_entries(category_name)
        
        wizards = {}
        for entry_name in entry_names:
            # We create the adapter with JUST the name. 
            # It will load the full entry only when called.
            wizards[entry_name] = CatalogWizardAdapter(entry_name)
                
        return wizards

    def get_commands(self) -> Dict[str, Callable]:
        """Catalog modules don't have secondary commands yet."""
        return {}
