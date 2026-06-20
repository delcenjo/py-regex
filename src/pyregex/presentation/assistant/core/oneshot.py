"""Nebula — One-Shot Wizard Executor.

Enables running a single wizard without entering the full REPL.
Used by `px create`, `px email`, `px phone`, etc.
"""

from __future__ import annotations
from typing import Any

from pyregex.domain.catalog.registry import catalog_registry
from pyregex.utils import ansi

def get_shortcut_map() -> dict[str, str]:
    """Returns a map of entry names to entries for quick lookup."""
    return {name: name for name in catalog_registry.list_entries()}

def get_category_map() -> dict[str, str]:
    """Returns a map of category names."""
    return {cat: cat for cat in catalog_registry.list_categories()}


def run_wizard_oneshot(shortcut: str, cli: Any = None) -> int:
    """Run a single wizard by shortcut name, then exit (AHA Architecture)."""
    shortcut = shortcut.lower().strip()

    entry = catalog_registry.get_entry(shortcut)

    if not entry and shortcut in catalog_registry.list_categories():
        return _show_category_menu(shortcut, cli)

    aliases = {"ipv4": "ip", "ipv6": "ip", "dom": "domain", "usr": "username", "md": "markdown_heading"}
    if not entry and shortcut in aliases:
        entry = catalog_registry.get_entry(aliases[shortcut])

    if entry:
        from pyregex.presentation.assistant.wizards.dynamic import DynamicWizard
        wizard = DynamicWizard(entry, cli)
        try:
            wizard.execute()
            return 0
        except KeyboardInterrupt:
            print(f"\n  {ansi.dim('Cancelado.')}")
            return 0
        except Exception as e:
            print(f"\n  {ansi.error('')} Error: {e}")
            return 1

    print(f"  {ansi.error('')} Comando o categoría desconocida: '{shortcut}'")
    return 1


def _show_category_menu(category: str, cli: Any = None) -> int:
    """Show a dynamic category menu using CatalogRegistry."""
    from prompt_toolkit import prompt as pt_prompt
    from prompt_toolkit.completion import WordCompleter

    entries = catalog_registry.list_entries(category)
    if not entries:
        print(f"  {ansi.error('')} Categoría vacía o no encontrada: {category}")
        return 1

    print(f"\n  {ansi.bold(category.title())}")
    print(f"  {ansi.dim(f'Explorando wizards en {category}')}\n")

    for i, name in enumerate(entries, 1):
        entry = catalog_registry.get_entry(name)
        display = entry.wizard.get("display_name", name) if entry else name
        desc = entry.description if entry else ""
        print(f"    [{i:2d}] {display:20s} {ansi.dim(desc)}")
    print(f"    [ q] {'Salir':20s}")

    completer = WordCompleter([str(i) for i in range(1, len(entries) + 1)] + entries + ["q"])
    choice = pt_prompt("> ", completer=completer).strip().lower()

    if choice == "q" or not choice:
        return 0

    target_wizard = None
    if choice.isdigit() and 1 <= int(choice) <= len(entries):
        target_wizard = entries[int(choice) - 1]
    elif choice in entries:
        target_wizard = choice

    if target_wizard:
        return run_wizard_oneshot(target_wizard, cli)

    print(f"  {ansi.error('')} Opción inválida")
    return 1
