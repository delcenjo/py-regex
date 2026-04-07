"""Nebula Shell — Professional REPL."""

from __future__ import annotations
from typing import Any, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from pathlib import Path

from pyregex.presentation.assistant.core.engine import AssistantEngine
from pyregex.presentation.assistant.core.config import AssistantConfig
from pyregex.presentation.assistant.core.types import SessionState
from pyregex.presentation.assistant.shell.completer import NebulaCompleter
from pyregex.presentation.assistant.shell.toolbar import StatusToolbar
from pyregex.presentation.assistant.shell.themes import get_theme
from pyregex.presentation.assistant.ui.components import Table, Panel, Menu
from pyregex.presentation.assistant.shell.keybindings import create_keybindings
from pyregex.presentation.assistant.shell.banner import show_banner, show_goodbye
from pyregex.utils import ansi

# Import all modules to trigger @register_module decorators


class NebulaREPL:
    """
    Professional interactive REPL for the Nebula Assistant Engine.

    Features:
    - Context-aware autocompletion
    - Dynamic toolbar with state/breadcrumbs
    - Custom keybindings (Ctrl+B=back, Ctrl+H=help)
    - Color themes (dark, light, monokai, nord)
    - Persistent command history
    - Banner with tips
    """

    def __init__(self, cli: Any = None, config: Optional[AssistantConfig] = None):
        self.config = config or AssistantConfig()
        self.theme = get_theme(self.config.theme)

        # Initialize engine
        self.engine = AssistantEngine(cli, self.config)

        # History
        history_path = Path.home() / ".pyregex" / "nebula_history"
        history_path.parent.mkdir(parents=True, exist_ok=True)

        # Completer
        self.completer = NebulaCompleter(
            registry=self.engine.registry,
            session=self.engine.session,
            fsm=self.engine.fsm,
        )

        # Toolbar
        self.toolbar = StatusToolbar(
            session=self.engine.session, fsm=self.engine.fsm, theme=self.theme
        )

        # Prompt session
        self.prompt_session = PromptSession(
            history=FileHistory(str(history_path)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.completer,
            complete_while_typing=True,
            key_bindings=create_keybindings(),
            bottom_toolbar=self.toolbar if self.config.show_toolbar else None,
        )

    def run(self, initial_command: Optional[str] = None) -> None:
        """Main REPL loop."""
        # Show banner
        if self.config.show_banner and not initial_command:
            total_wizards = sum(
                len(self.engine.registry.get(n).get_wizards())
                for n in self.engine.registry.names
            )
            show_banner(
                module_count=self.engine.registry.count, wizard_count=total_wizards
            )

        # Start FSM
        self.engine.fsm.trigger("start")

        if initial_command:
            response = self.engine.process_input(initial_command)
            self._handle_response(response, initial_command)

        # Main loop
        while True:
            try:
                # Build dynamic prompt
                prompt_text = self._build_prompt()

                # Get input
                user_input = self.prompt_session.prompt(prompt_text)

                if not user_input.strip():
                    continue

                # Process through engine
                response = self.engine.process_input(user_input)

                # Handle response
                self._handle_response(response, user_input)

            except KeyboardInterrupt:
                print(
                    f"\n  {ansi.dim('(Ctrl+C para cancelar, escribe quit para salir)')}"
                )
                continue
            except EOFError:
                break

        # Cleanup
        self.engine.shutdown()
        show_goodbye()

    def _build_prompt(self) -> HTML:
        """Build the dynamic prompt based on current state (Expert Style)."""
        state = self.engine.fsm.state
        breadcrumbs = self.engine.session.breadcrumb_str
        
        # Expert palette mapping
        theme = self.theme
        
        if state == SessionState.BROWSING:
            return HTML(
                f"<b><ansiblue>nebula</ansiblue></b> <ansipurple>»</ansipurple> "
            )
        elif state == SessionState.IN_MODULE:
            module = self.engine.session.current_module or "?"
            return HTML(
                f"<b><ansiblue>nebula</ansiblue></b><ansiwhite>/</ansiwhite><ansigreen>{module}</ansigreen> <ansipurple>»</ansipurple> "
            )
        elif state == SessionState.IN_WIZARD:
            wizard = self.engine.session.current_wizard or "?"
            return HTML(
                f"<b><ansiblue>nebula</ansiblue></b><ansiwhite>/</ansiwhite><ansiyellow>{wizard}</ansiyellow> <ansipurple>»</ansipurple> "
            )
        elif state == SessionState.BROWSING_CATALOG:
            path = self.engine.session.catalog_path
            path_str = "…/" + path[-1] if len(path) > 2 else "/".join(path)
            return HTML(
                f"<b><ansiblue>nebula</ansiblue></b><ansiwhite>/</ansiwhite><ansicyan>{path_str}</ansicyan> <ansipurple>»</ansipurple> "
            )
        else:
            return HTML(
                "<b><ansiblue>nebula</ansiblue></b> <ansipurple>»</ansipurple> "
            )

    def _handle_response(self, response, raw_input: str) -> None:
        """Handle engine response and display output."""
        if not response.success:
            if response.error:
                print(f"\n  {ansi.error('✗')} {response.error}")
            return

        result = response.result

        if result == "exit":
            self.engine.shutdown()
            show_goodbye()
            raise EOFError  # Exit the loop

        elif result == "back":
            pass  # State already handled by engine

        elif result == "clear":
            import os

            os.system("clear" if os.name == "posix" else "cls")

        elif result == "help":
            self._show_help()

        elif result == "history":
            self._show_history()

        elif isinstance(result, dict):
            if "category" in result:
                self._show_category(result)
            elif "module" in result:
                self._show_module(result)
            elif result.get("type") == "catalog_path":
                self._show_catalog_path(result)
            elif "selection" in result:
                print(f"  {ansi.dim('Menu selection: ' + str(result['selection']))}")
            else:
                # Stats or other dict
                for k, v in result.items():
                    print(f"  {ansi.bold(k)}: {v}")

        elif result == "ambiguous":
            print(f"\n  {ansi.warning('⚠')} Comando ambiguo. Opciones:")
            for w in response.warnings:
                print(f"    • {w}")

        # Show warnings
        for w in response.warnings:
            if result != "ambiguous":
                print(f"  {ansi.dim(w)}")

    def _show_help(self) -> None:
        """Display technical help architecture."""
        help_content = []
        for info in self.engine.registry.list_all():
            wizards = self.engine.registry.get(info.name).get_wizards()
            w_list = ", ".join(w.replace("_wizard", "") for w in wizards)
            help_content.append(f"{ansi.bold(info.display_name)}: {ansi.dim(w_list)}")

        Panel("\n".join(help_content), title="Nebula Registry Architecture").print()

        headers = ["Command", "Architecture Function"]
        rows = [
            ["help", "Access architectural primitives"],
            ["create", "Explore hierarchical regex catalog"],
            ["back", "Revert session state"],
            ["status", "Inspect session telemetry"],
            ["history", "Review command sequence"],
            ["clear", "Flush display buffer"],
            ["quit", "Terminate assistant context"],
        ]
        Table(headers, rows, title="System Commands").print()

    def _show_category(self, data: dict) -> None:
        """Display category modules using expert menu."""
        cat = data.get("category", "")
        modules = data.get("modules", [])
        
        items = [(str(i), m.display_name, m.description) for i, m in enumerate(modules, 1)]
        Menu(items, title=f"Category: {cat}").print()

    def _show_module(self, data: dict) -> None:
        """Display module wizards using expert system."""
        module_name = data.get("module", "")
        wizards = data.get("wizards", [])
        info = data.get("info")

        if info:
            Panel(info.description, title=f" {info.icon} {info.display_name} ").print()

        items = [(str(i), w.replace("_wizard", ""), "Technical wizard implementation") for i, w in enumerate(wizards, 1)]
        Menu(items, title="Available Primitives").print()
        print()

    def _show_history(self) -> None:
        """Display command history."""
        history = self.engine.session.history
        if not history:
            print(f"\n  {ansi.dim('Sin historial')}")
            return

        print(f"\n  {ansi.bold('Últimos comandos:')}")
        for entry in history[-15:]:
            print(f"    {ansi.dim(entry.timestamp[:19])} {entry.command}")

    def _show_catalog_path(self, data: dict) -> None:
        """Display catalog subfolders and entries in a professional table."""
        path = data.get("path", [])
        subfolders = data.get("subfolders", [])
        entries = data.get("entries", [])
        
        path_str = " / ".join(path) if path else "CATALOG ROOT"
        
        rows = []
        for folder in subfolders:
            rows.append([ansi.bold("DIR"), folder, "Hierarchical category"])
        for entry in entries:
            rows.append([ansi.bold("EXPR"), entry, "Wizard implementation"])
            
        Table(["Type", "Identifier", "Description"], rows, title=path_str).print()
