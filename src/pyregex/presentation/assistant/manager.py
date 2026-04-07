"""Manager for the PyRegex Interactive Assistant. orchestrates navigation and flow dispatching."""

from __future__ import annotations
import argparse
import re
from typing import Any, Optional

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

from pyregex.utils import ansi
from pyregex.i18n import translator as i18n
from pyregex.infrastructure.persistence.pattern_repository import SavedPattern
from pyregex.domain.builders.base import RegexBuilder

from pyregex.presentation.assistant.flows.utils import UtilsFlows
from pyregex.presentation.assistant.flows.actions import ActionFlows
from pyregex.presentation.assistant.wizards.dynamic import DynamicWizard
from pyregex.domain.catalog.registry import catalog_registry

# Import new modules for auto-discovery (side-effect: registers them)
try:
    import pyregex.presentation.assistant.modules.finance.module  # noqa: F401
    import pyregex.presentation.assistant.modules.security.module  # noqa: F401
    import pyregex.presentation.assistant.modules.devops.module  # noqa: F401
    import pyregex.presentation.assistant.modules.data.module  # noqa: F401
    import pyregex.presentation.assistant.modules.i18n.module  # noqa: F401
    import pyregex.presentation.assistant.modules.compliance.module  # noqa: F401
except ImportError:
    pass

# Display info for all 12 categories
_CATEGORY_DISPLAY = {
    "personal": "🧑 Datos Personales",
    "web": "🌐 Web & Red",
    "structured": "📋 Datos Estructurados",
    "systems": "🖥️ Sistemas",
    "utils": "🛠️ Utilidades",
    "finance": "🏦 Finanzas & Banca",
    "security": "🔐 Seguridad & Auth",
    "devops": "⚙️ DevOps & IaC",
    "data": "📊 Data & Formatos",
    "i18n": "🌍 Internacionalización",
    "compliance": "⚖️ Compliance & Legal",
}


class AssistantManager:
    """Orchestrates the interactive assistant flows and navigation menu."""

    def __init__(self, cli: Any):
        self.cli = cli
        self.utils = UtilsFlows(cli)
        self.actions = ActionFlows(cli)

    def run(self, args: argparse.Namespace | None = None) -> int:
        """Main entry point for the interactive assistant."""
        if args and args.command:
            # Check if command is a dynamic catalog category or a shortcut
            if args.command in catalog_registry.list_categories() or args.command in [
                "utils", "email", "phone", "url", "ip", "logs", "aws", "docker", "k8s", "edit", "secure"
            ]:
                return self.dispatch(args)

        ansi.print_banner(i18n.t("assistant.menu_title"))

        while True:
            # Main Category Menu — Dynamic with all categories
            print(f"\n{ansi.bold(i18n.t('assistant.select_type'))}")
            categories = list(_CATEGORY_DISPLAY.keys())
            for i, cat in enumerate(categories, 1):
                label = _CATEGORY_DISPLAY.get(cat, cat)
                print(f" [{i:2d}] {label}")
            print(f" [ q] {i18n.t('common.quit')}")

            cat_completer = WordCompleter(
                [str(i) for i in range(1, len(categories) + 1)] + ["q"], ignore_case=True
            )
            cat_choice = prompt("> ", completer=cat_completer).strip().lower()

            if cat_choice == "q" or not cat_choice:
                return 0

            if not cat_choice.isdigit() or not (1 <= int(cat_choice) <= len(categories)):
                print(ansi.error(i18n.t("assistant.invalid_choice")))
                continue

            category = categories[int(cat_choice) - 1]
            if not self._handle_category(category, args):
                continue

            # If we were in single-command mode (via args), we might want to exit after one flow.
            # But usually the assistant is'interactive. cmd_create in cli.py returns 0 after one flow if it finishes.
            # However, the loop in cli.py (line 725) is 'while True'.
            # But line 946 says 'return 0' inside the loop? Wait.
            # Let's re-check cli.py line 946.

            # Re-checking cli.py:
            # 946:             return 0
            # That 'return 0' is INSIDE the while True loop (line 725) at the same indentation level as the choice dispatch.
            # So it exits after ONE pattern is generated and handled.
            return 0

    def dispatch(self, args: argparse.Namespace) -> int:
        """Dispatches an advanced shortcut command to the relevant flow handler."""
        cmd = args.command
        sub = getattr(args, "subtype", None)

        target = sub if sub else cmd

        # 1. Action & Utility Commands
        if cmd == "utils" or cmd in ["edit", "hist", "custom", "merge", "perf", "c", "w", "token", "time", "date"]:
            if target == "hist":
                self.actions.handle_hist_flow(args)
                return 0
            
            # Map legacy shortcuts directly to Hybrid Engine Dynamic Wizards
            shortcut_map = {
                "c": ("systems", "color"),
                "w": ("security", "password"),
                "token": ("devops", "token"),
                "time": ("systems", "time"),
                "date": ("systems", "date")
            }
            if target in shortcut_map:
                cat, sub = shortcut_map[target]
                return self._handle_wizard_category(cat, sub, args)
            
            method_map = {
                "edit": "handle_edit_flow",
                "custom": "handle_custom_flow",
                "merge": "handle_merge_flow",
                "perf": "handle_perf_flow",
            }
            if target in method_map:
                if target == "perf":
                    self.utils.handle_perf_flow(args)
                elif target == "edit":
                    pattern = getattr(args, "pattern", None)
                    if not pattern:
                        pattern = prompt("Regex: ").strip()
                    if pattern:
                        self.actions.handle_edit_flow(pattern, args=args)
                else:
                    handler = self.actions
                    if target == "custom":
                        handler = self.utils
                    getattr(handler, method_map[target])(args)
            return 0

        # 2. Dynamic Discovery (Hybrid Engine)
        # Check both direct name and category-qualified name
        entry = catalog_registry.get_entry(target)
        if not entry and sub:
            # Try combining category and subtype (e.g. personal.email)
            entry = catalog_registry.get_entry(f"{cmd}.{sub}")
        
        if entry:
            wizard = DynamicWizard(entry, self.cli)
            wizard.execute()
            return 0

        # 3. Handle specific legacy aliases (forward to dynamic)
        legacy_aliases = {"ipv4": "ip", "domain": "dom"}
        if target in legacy_aliases:
            return self.dispatch(argparse.Namespace(command=cmd, subtype=legacy_aliases[target]))

        print(ansi.error(f"Unknown command or legacy builder not found: {target}"))
        return 1

    def _handle_category(
        self, category: str, args: argparse.Namespace | None = None
    ) -> bool:
        """Handles sub-menu and dispatching for a specific category using the Hybrid Engine."""
        # 1. Action & Utility Categories (Hardcoded interactive menus for non-regex utilities)
        if category == "utils":
            items = ["edit", "hist", "custom", "merge", "perf", "c", "w", "token", "time", "date"]
            cat_label = _CATEGORY_DISPLAY.get(category, category)
            print(f"\n{ansi.label(cat_label)}:")
            for item in items:
                label = i18n.t(f"assistant.types.{item}") if i18n.has(f"assistant.types.{item}") else item.replace('_', ' ').title()
                print(f" [{item}] {label}")
            print(f" [b] {i18n.t('common.back') if i18n.has('common.back') else 'Volver'}")

            item_completer = WordCompleter(items + ["b"], ignore_case=True)
            choice = prompt("> ", completer=item_completer).strip().lower()

            if choice == "b": return False
            if choice not in items:
                print(ansi.error(i18n.t("assistant.invalid_choice")))
                return False

            if choice == "hist":
                self.actions.handle_hist_flow(args)
                return True

            # Specialized routing for shortcuts within the utils menu
            shortcut_map = {
                "c": ("systems", "color"),
                "w": ("security", "password"),
                "token": ("devops", "token"),
                "time": ("systems", "time"),
                "date": ("systems", "date")
            }
            if choice in shortcut_map:
                cat, sub = shortcut_map[choice]
                return self._handle_wizard_category(cat, sub, args)

            method_map = {
                "edit": "handle_edit_flow",
                "custom": "handle_custom_flow",
                "merge": "handle_merge_flow",
                "perf": "handle_perf_flow",
            }
            if choice == "perf":
                self.utils.handle_perf_flow(args)
            elif choice == "custom":
                self.utils.handle_custom_flow(args)
            elif choice == "edit":
                print(ansi.info("Load a pattern first to edit it, or enter a custom one."))
                pattern = prompt("Regex: ").strip()
                if pattern:
                    self.actions.handle_edit_flow(pattern, args=args)
            elif choice == "merge":
                self.actions.handle_merge_flow(args)
            return True

        # 2. Dynamic Discovery (Hybrid Engine)
        items = catalog_registry.list_entries(category)
        if not items:
            print(ansi.error(f"No entries configured for category: {category}"))
            return False

        cat_label = _CATEGORY_DISPLAY.get(category, category)
        print(f"\n{ansi.label(cat_label)}:")
        for item in items:
            entry = catalog_registry.get_entry(item)
            name = entry.wizard.get("display_name", item) if entry else item
            print(f" [{item}] {name}")
        print(f" [b] {i18n.t('common.back') if i18n.has('common.back') else 'Volver'}")

        item_completer = WordCompleter(items + ["b"], ignore_case=True)
        choice = prompt("> ", completer=item_completer).strip().lower()

        if choice == "b": return False
        if choice not in items:
            print(ansi.error(i18n.t("assistant.invalid_choice")))
            return False

        return self._handle_wizard_category(category, choice)

    def _handle_wizard_category(self, category: str, choice: str, args: argparse.Namespace | None = None) -> bool:
        """Handles wizard-based dispatch using the dynamic CatalogRegistry."""
        entry = catalog_registry.get_entry(choice)
        
        if not entry:
            print(ansi.error(f"Unknown command: {choice}"))
            return False

        # Create the dynamic wizard from the catalog entry
        wizard = DynamicWizard(entry, self.cli)
        
        # Execute the wizard (it handles its own runner and finalization)
        wizard.execute()
        
        return True
