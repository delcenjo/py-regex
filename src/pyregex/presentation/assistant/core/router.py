"""Nebula Assistant Engine — Command Router."""

from __future__ import annotations
from typing import Optional

from pyregex.presentation.assistant.core.types import ModuleCategory
from pyregex.presentation.assistant.core.registry import ModuleRegistry
from pyregex.presentation.assistant.core.events import EventBus


class Router:
    """
    Maps user input to module + wizard targets.

    Supports:
    - Direct command routing (e.g., "email" → personal/email_wizard)
    - Category browsing (e.g., "personal" → show personal sub-menu)
    - Alias resolution (e.g., "cc" → credit_card_wizard)
    - Fuzzy matching for typos
    """

    def __init__(self, registry: ModuleRegistry, event_bus: Optional[EventBus] = None):
        self._registry = registry
        self._event_bus = event_bus
        self._aliases: dict[
            str, tuple[str, str]
        ] = {}  # alias → (module_name, wizard_name)
        self._shortcuts: dict[str, str] = {}  # shortcut → category

    def register_alias(self, alias: str, module_name: str, wizard_name: str) -> None:
        """Register a direct alias for a specific wizard."""
        self._aliases[alias.lower()] = (module_name, wizard_name)

    def register_shortcut(self, shortcut: str, category: str) -> None:
        """Register a shortcut for a category."""
        self._shortcuts[shortcut.lower()] = category

    def resolve(self, input_text: str) -> RouteResult:
        """
        Resolve user input to a route target.

        Resolution order:
        1. Built-in commands (help, exit, history, etc.)
        2. Direct aliases (email, phone, url, etc.)
        3. Category shortcuts (personal, web, etc.)
        4. Module name match
        5. Fuzzy search across module descriptions
        """
        text = input_text.strip().lower()

        # 1. Built-in commands
        builtins = {
            "help": RouteResult(RouteType.BUILTIN, command="help"),
            "exit": RouteResult(RouteType.EXIT),
            "quit": RouteResult(RouteType.EXIT),
            "q": RouteResult(RouteType.EXIT),
            "back": RouteResult(RouteType.BACK),
            "b": RouteResult(RouteType.BACK),
            "history": RouteResult(RouteType.BUILTIN, command="history"),
            "clear": RouteResult(RouteType.BUILTIN, command="clear"),
            "status": RouteResult(RouteType.BUILTIN, command="status"),
            "create": RouteResult(RouteType.CREATE),
            "undo": RouteResult(RouteType.BUILTIN, command="undo"),
            "redo": RouteResult(RouteType.BUILTIN, command="redo"),
        }
        if text in builtins:
            return builtins[text]

        # 2. Direct aliases (manual overrides and abbreviations)
        if text in self._aliases:
            module_name, wizard_name = self._aliases[text]
            return RouteResult(RouteType.WIZARD, module=module_name, wizard=wizard_name)

        # 3. Dynamic Resolution — check every module for a wizard matching this name
        # If the input is in the discovery index, we route it directly
        from pyregex.domain.catalog.registry import catalog_registry
        if text in catalog_registry._discovery_map:
            # We determine the category from the categories map
            for cat, entries in catalog_registry._categories.items():
                if text in entries:
                    return RouteResult(RouteType.WIZARD, module=cat, wizard=text)
                    
        # 3.5 Fallback for manual module wizards (that are not in the catalog)
        for info in self._registry.list_all():
            # Skip catalog modules here as we already checked the index
            if hasattr(self._registry.get(info.name), "wizard_count"):
                continue
            try:
                module = self._registry.get(info.name)
                wizards = module.get_wizards()
                for wiz_full_name in wizards:
                    wiz_short_name = wiz_full_name.replace("_wizard", "").lower()
                    if text == wiz_short_name:
                        return RouteResult(RouteType.WIZARD, module=info.name, wizard=wiz_full_name)
            except Exception:
                continue

        # 4. Category shortcuts
        if text in self._shortcuts:
            return RouteResult(RouteType.CATEGORY, category=self._shortcuts[text])

        # 5. Category enum match
        for cat in ModuleCategory:
            if text == cat.value:
                return RouteResult(RouteType.CATEGORY, category=cat.value)

        # 6. Module name direct match
        if text in self._registry:
            module = self._registry.get(text)
            return RouteResult(RouteType.MODULE, module=text)

        # 7. Numeric input (menu selection)
        if text.isdigit():
            return RouteResult(RouteType.MENU_SELECT, command=text)

        # 8. Fuzzy search
        matches = self._registry.search(text)
        if len(matches) == 1:
            return RouteResult(RouteType.MODULE, module=matches[0].name)
        elif len(matches) > 1:
            return RouteResult(
                RouteType.AMBIGUOUS, suggestions=[m.name for m in matches]
            )

        # 9. Unrecognized
        return RouteResult(RouteType.UNKNOWN, command=text)

    def setup_default_aliases(self) -> None:
        """Register standard aliases for common patterns.

        Automatically registers every wizard as a direct command,
        plus maintains common abbreviations.
        """
        # 1. Dynamic Registration — ONLY for manual modules (not catalog)
        for info in self._registry.list_all():
            try:
                module = self._registry.get(info.name)
                # Skip CatalogModules to avoid loading 28k files
                if hasattr(module, "wizard_count"):
                    continue
                    
                wizards = module.get_wizards()
                for wiz_name in wizards:
                    # e.g. "email_wizard" -> "email"
                    alias = wiz_name.replace("_wizard", "")
                    self.register_alias(alias, info.name, wiz_name)
            except Exception:
                continue

        # 2. Hand-crafted abbreviations and special cases
        # These override or supplement the generic aliases
        special_cases = {
            # Personal
            "cc": ("personal", "credit_card_wizard"),
            "card": ("personal", "credit_card_wizard"),
            "zip": ("personal", "postal_wizard"),
            "adr": ("personal", "address_wizard"),
            "usr": ("personal", "username_wizard"),
            # Web
            "dom": ("web", "domain_wizard"),
            "ipv4": ("web", "ip_wizard"),
            "ipv6": ("web", "ip_wizard"),
            # DevOps
            "ci": ("devops", "cicd_wizard"),
            "tf": ("devops", "terraform_wizard"),
            "plate": ("devops", "license_plate_wizard"),
            # Finance
            "bic": ("finance", "swift_wizard"),
            "money": ("finance", "currency_wizard"),
            "factura": ("finance", "invoice_wizard"),
            "bank": ("finance", "bank_account_wizard"),
            "bitcoin": ("finance", "crypto_wizard"),
            "nif": ("finance", "tax_id_wizard"),
            # Security
            "certificate": ("security", "cert_wizard"),
            "gdpr": ("security", "pii_wizard"),
            # Compliance
            "icd": ("compliance", "medical_wizard"),
            "boe": ("compliance", "legal_wizard"),
            "iso": ("compliance", "iso_standard_wizard"),
            # Structured/Systems
            "num": ("structured", "number_wizard"),
            "err": ("systems", "error_wizard"),
            "edit": ("tools", "editor_wizard"),
        }

        for alias, (mod, wiz) in special_cases.items():
            self.register_alias(alias, mod, wiz)

        # 3. Category shortcuts
        for cat in ModuleCategory:
            self.register_shortcut(cat.value, cat.value)


# ── Route Result ─────────────────────────────────────────────────────

from enum import Enum, auto


class RouteType(Enum):
    """Types of route resolution results."""

    WIZARD = auto()  # Direct to a specific wizard
    MODULE = auto()  # Navigate to a module
    CATEGORY = auto()  # Browse a category
    CREATE = auto()  # Start hierarchical catalog browsing
    BUILTIN = auto()  # Built-in command
    MENU_SELECT = auto()  # Numeric menu selection
    BACK = auto()  # Go back
    EXIT = auto()  # Exit assistant
    AMBIGUOUS = auto()  # Multiple matches
    UNKNOWN = auto()  # Unrecognized input


class RouteResult:
    """Result of route resolution."""

    def __init__(
        self,
        route_type: RouteType,
        module: str = "",
        wizard: str = "",
        category: str = "",
        command: str = "",
        suggestions: list[str] | None = None,
    ):
        self.type = route_type
        self.module = module
        self.wizard = wizard
        self.category = category
        self.command = command
        self.suggestions = suggestions or []
