"""Nebula Shell — Context-Aware Completer."""

from __future__ import annotations

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document

from pyregex.presentation.assistant.core.session import SessionContext
from pyregex.presentation.assistant.core.registry import ModuleRegistry
from pyregex.presentation.assistant.core.state.machine import StateMachine
from pyregex.presentation.assistant.core.types import SessionState


class NebulaCompleter(Completer):
    """
    Context-aware autocompletion for the assistant REPL.

    Completions change based on the current FSM state:
    - IDLE/BROWSING: categories, module names, built-in commands
    - IN_MODULE: wizard names from the current module
    - Always: 'help', 'back', 'quit', 'status', 'history'
    """

    BUILTINS = {
        "help": "Show help and available commands",
        "back": "Go back to previous screen",
        "quit": "Exit the assistant",
        "exit": "Exit the assistant",
        "status": "Show session statistics",
        "history": "Show command history",
        "clear": "Clear the screen",
        "undo": "Undo last action",
        "redo": "Redo last action",
    }

    def __init__(
        self, registry: ModuleRegistry, session: SessionContext, fsm: StateMachine
    ):
        self._registry = registry
        self._session = session
        self._fsm = fsm
        self._cached_shortcuts: list[tuple[str, str]] = []  # [(display_name, category_display)]

    def _get_all_shortcuts(self) -> list[tuple[str, str]]:
        """Lazily load manual module shortcuts (Excluding 28k+ catalog entries)."""
        if not self._cached_shortcuts:
            for info in self._registry.list_all():
                # Skip catalog modules for global shortcuts to prevent O(N) memory/cpu hit
                if info.name in ("health", "security", "devops", "finance", "legal", "science", "media", "social", "transport", "utils"):
                    continue
                try:
                    module = self._registry.get(info.name)
                    wizards = module.get_wizards()
                    for wiz_name in wizards:
                        display = wiz_name.replace("_wizard", "")
                        self._cached_shortcuts.append((display, info.display_name))
                except Exception:
                    continue
        return self._cached_shortcuts

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor.strip().lower()
        state = self._fsm.state

        for cmd, desc in self.BUILTINS.items():
            if cmd.startswith(text):
                yield Completion(cmd, start_position=-len(text), display_meta=desc)

        # Special case: 'create' command in IDLE/BROWSING
        if "create".startswith(text) and state in (SessionState.IDLE, SessionState.BROWSING):
            yield Completion("create", start_position=-len(text), display_meta="Explorar catálogo")

        # 1. Main Prompt Completions (IDLE/BROWSING)
        if state in (SessionState.IDLE, SessionState.BROWSING):
            # Categories & Modules
            for cat_enum in self._registry.list_categories():
                cat_name = cat_enum.value
                if cat_name.startswith(text):
                    modules = self._registry.get_by_category(cat_enum)
                    desc = modules[0].info.display_name if modules else f"Categoría {cat_name}"
                    yield Completion(cat_name, start_position=-len(text), display_meta=desc)
            
            # NOTE: Global discovery of 28,000+ wizards is disabled at root 
            # to maintain performance. Use 'create' or browse modules of interest.

        # 1.5 Catalog Browsing Completions
        elif state == SessionState.BROWSING_CATALOG:
            from pyregex.domain.catalog.registry import catalog_registry
            path = self._session.catalog_path
            subfolders, entries = catalog_registry.list_at_path(path)
            
            for folder in subfolders:
                if folder.startswith(text):
                    yield Completion(folder, start_position=-len(text), display_meta="Carpeta")
            
            for entry in entries:
                if entry.startswith(text):
                    yield Completion(entry, start_position=-len(text), display_meta="Wizard")

        # 2. In-module Prompt Completions
        elif state == SessionState.IN_MODULE:
            current_module = self._session.current_module
            if current_module and current_module in self._registry:
                module = self._registry.get(current_module)
                try:
                    entry_names = module.get_wizards().keys()
                    # Limit completions for massive categories to avoid UI lag
                    count = 0
                    for wiz_name in entry_names:
                        if count > 100 and not text: # Only show first 100 if no filter
                            break
                        display = wiz_name.replace("_wizard", "")
                        if not text or text in display or text in wiz_name:
                            yield Completion(
                                display, start_position=-len(text), display_meta=wiz_name
                            )
                            count += 1
                except Exception:
                    pass

        # 3. Fuzzy search fallback (only for 2+ chars)
        if len(text) >= 2 and state not in (SessionState.IN_WIZARD,):
            for info in self._registry.search(text):
                if info.name != text:
                    yield Completion(
                        info.name,
                        start_position=-len(text),
                        display_meta=info.description[:40],
                    )
