"""Main CLI implementation for PyRegex."""

from __future__ import annotations

import argparse
import sys
import json
from typing import Any, Optional, List

from pyregex.infrastructure.registry import registry

from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

# Advanced Services
from pyregex.core.shared.exceptions import (
    PyRegexError,
    ExecutionTimeoutError,
    PatternNotFoundError,
)
from pyregex.utils import ansi
from pyregex.i18n import translator as i18n
from pyregex.presentation.cli.dispatcher import CommandDispatcher
from pyregex.presentation.cli.test import TestCommand
from pyregex.presentation.cli.explain import ExplainCommand
from pyregex.presentation.cli.save import SaveCommand
from pyregex.presentation.cli.list import ListCommand
from pyregex.presentation.cli.delete import DeleteCommand
from pyregex.presentation.cli.run import RunCommand


class PyRegexParser(argparse.ArgumentParser):
    """Custom parser that doesn't exit on error (important for REPL)."""

    def error(self, message: str):
        """Override error to raise an exception instead of exiting."""
        raise argparse.ArgumentError(None, message)

    def exit(self, status=0, message=None):
        """Override exit to raise an exception instead of exiting."""
        if message:
            self._print_message(message, sys.stderr)
        raise SystemExit(status)


from pyregex.container import AppContainer

class PyRegexCLI:
    """Coordinates all components and handles user commands."""

    def __init__(self, container: AppContainer):
        self.container = container
        self.config = container.config
        self.config_repo = container.config_repo
        self.pattern_repo = container.pattern_repo
        self.history_repo = container.history_repo
        self.catalog = container.catalog

        # Galaxy Architecture: Modular Command Dispatcher (Lazy)
        self.dispatcher = CommandDispatcher()
        self._register_commands()

        # Use dependencies from container
        self.registry = self.catalog
        self._current_merged_pattern: Optional[str] = None

    @property
    def assistant(self):
        if not hasattr(self, "_assistant"):
            from pyregex.presentation.assistant.manager import AssistantManager
            self._assistant = AssistantManager(self)
        return self._assistant

    # ── Lazy Loaded Services ───────────────────────────────────────

    @property
    def perf_service(self):
        if not hasattr(self, "_perf_service"):
            from pyregex.application.services.performance_service import RegexPerformanceService
            self._perf_service = RegexPerformanceService()
        return self._perf_service

    @property
    def merge_service(self):
        if not hasattr(self, "_merge_service"):
            from pyregex.application.services.merge_service import RegexMergeService
            self._merge_service = RegexMergeService()
        return self._merge_service

    @property
    def editor_service(self):
        if not hasattr(self, "_editor_service"):
            from pyregex.application.services.editor_service import RegexEditorService
            self._editor_service = RegexEditorService()
        return self._editor_service

    @property
    def security_service(self):
        if not hasattr(self, "_security_service"):
            from pyregex.application.security.security_service import SecurityService
            self._security_service = SecurityService()
        return self._security_service

    @property
    def quick_controller(self):
        if not hasattr(self, "_quick_controller"):
            from pyregex.application.services.quick.controller.quick_controller import QuickController
            self._quick_controller = QuickController(registry)
        return self._quick_controller

    @property
    def testing_controller(self):
        if not hasattr(self, "_testing_controller"):
            from pyregex.application.services.testing.controller.testing_controller import TestingController
            self._testing_controller = TestingController(self.quick_controller)
        return self._testing_controller

    @property
    def explain_system(self):
        if not hasattr(self, "_explain_system"):
            from pyregex.application.services.explain_controller import ExplainController
            self._explain_system = ExplainController()
        return self._explain_system

    @property
    def registry_system(self):
        if not hasattr(self, "_registry_system"):
            from pyregex.application.services.registry_controller import RegistryController
            self._registry_system = RegistryController()
        return self._registry_system

    @property
    def execution_system(self):
        if not hasattr(self, "_execution_system"):
            from pyregex.application.services.execution.execution_controller import ExecutionController
            self._execution_system = ExecutionController(self.registry_system)
        return self._execution_system

    @property
    def service(self):
        if not hasattr(self, "_service"):
            from pyregex.application.services.regex_service import RegexService
            self._service = RegexService(region=self.config.region)
        return self._service

    @property
    def explainer(self):
        if not hasattr(self, "_explainer"):
            from pyregex.domain.explain.engine import AdvancedExplainer
            self._explainer = AdvancedExplainer()
        return self._explainer

    @property
    def highlighter(self):
        if not hasattr(self, "_highlighter"):
            from pyregex.application.services.testing.visualization.highlighter import TestingHighlighter
            self._highlighter = TestingHighlighter()
        return self._highlighter

    def _register_commands(self):
        """Registers all modular commands to the dispatcher (Now Lazy-Enabled)."""
        # Dynamic command loading via local imports in each command class 
        # is handled by the dispatcher during dispatch time.
        # Here we only register the metadata and the COMMAND CLASSES.
        
        from pyregex.presentation.cli.audit import AuditCommand
        from pyregex.presentation.cli.mask import MaskCommand
        from pyregex.presentation.cli.validate import ValidateCommand
        from pyregex.presentation.cli.transform import TransformCommand
        from pyregex.presentation.cli.generate import GenerateCommand
        from pyregex.presentation.cli.learn import LearnCommand
        from pyregex.presentation.cli.bench import BenchCommand
        from pyregex.presentation.cli.history import HistoryCommand
        from pyregex.presentation.cli.config import ConfigCommand
        from pyregex.presentation.cli.export import ExportCommand
        from pyregex.presentation.cli.extract import ExtractCommand
        from pyregex.presentation.cli.replace import ReplaceCommand
        from pyregex.presentation.cli.create import CreateCommand

        # In a real 'Lightning' system, we could also use a map
        # to avoid instantiating these until DISPATCH.
        # For now, instantiating these classes is cheap enough.
        commands = [
            TestCommand(), ExplainCommand(), SaveCommand(),
            ListCommand(), DeleteCommand(), RunCommand(),
            AuditCommand(), MaskCommand(), ValidateCommand(),
            TransformCommand(), GenerateCommand(), LearnCommand(),
            BenchCommand(), HistoryCommand(), ConfigCommand(),
            ExportCommand(), ExtractCommand(), ReplaceCommand(),
            CreateCommand(),
        ]

        for cmd in commands:
            self.dispatcher.register(cmd)

    def _get_arg_or_prompt(
        self,
        args: argparse.Namespace | None,
        arg_name: str,
        prompt_key: str,
        options: list[str] | None = None,
        default: str | None = None,
    ) -> str:
        """Helper to get a parameter from the CLI args or prompt the user."""
        val = getattr(args, arg_name, None) if args else None
        if val is not None:
            return str(val).strip().lower()

        prompt_msg = i18n.t(prompt_key) if i18n.has(prompt_key) else prompt_key
        completer = WordCompleter(options) if options else None
        return prompt(f"{prompt_msg} ", completer=completer).strip().lower() or (
            default or ""
        )

    def _setup_advanced_subparsers(self, subparsers: Any) -> None:
        """Dynamic discovery of all catalog categories and wizards (AHA Architecture)."""
        from pyregex.domain.catalog.registry import catalog_registry

        # 1. Discover all categories in the catalog
        for cat_name in catalog_registry.list_categories():
            # Get category metadata (could be in YAML in the future)
            cat_help = f"{cat_name.title()} patterns and wizards"
            
            p_cat = subparsers.add_parser(cat_name, help=cat_help)
            p_cat_s = p_cat.add_subparsers(dest="subtype", help=f"{cat_name} type")

            # 2. Discover all wizards within this category
            for entry_name in catalog_registry.list_entries(cat_name):
                entry = catalog_registry.get_entry(entry_name)
                if not entry:
                    continue
                
                display_name = entry.wizard.get("display_name", entry_name)
                p_wiz = p_cat_s.add_parser(entry_name, help=entry.description or display_name)
                
                # 3. Dynamic Arguments from config_schema (90/10 Logic)
                # If the entry has a schema, we add the arguments to the CLI
                schema = entry.wizard.get("config_schema", {})
                for arg_name, arg_cfg in schema.items():
                    arg_help = arg_cfg.get("title", arg_name)
                    choices = [c[0] for c in arg_cfg.get("choices", [])] if "choices" in arg_cfg else None
                    
                    # We add them as optional flags
                    p_wiz.add_argument(f"--{arg_name}", choices=choices, help=arg_help)

        # 4. Top-Level Shortcuts (Important for UX)
        # We can also make these dynamic later, but keeping common ones for now.
        common_shortcuts = ["email", "phone", "url", "ip", "logs", "aws", "docker", "k8s"]
        for sc in common_shortcuts:
            try:
                subparsers.add_parser(sc, help=f"Shortcut for {sc}")
            except Exception:
                # Might already exist as a category
                continue

    def _dispatch_advanced_command(self, args: argparse.Namespace) -> int:
        """Dispatches an advanced shortcut command to the relevant flow handler."""
        return self.assistant.dispatch(args)

    def run(self, argv: Optional[List[str]] = None) -> int:
        if argv is None:
            argv = sys.argv[1:]

        # print(f"DEBUG: PyRegexCLI.run(argv={argv})") # Temporarily disabled

        if not argv:
            from pyregex.presentation.shell.shell import PyRegexShell
            shell = PyRegexShell(self)
            shell.run()
            return 0

        commands = [
            "create",
            "test",
            "explain",
            "save",
            "list",
            "delete",
            "run",
            "config",
            "export",
            "history",
            "extract",
            "replace",
            "bench",
            "audit",
            "mask",
            "validate",
            "transform",
            "generate",
            "learn",
        ]

        # Standard CLI routing...

        # If the first argument is not a command or flag, treat it as a quick intent
        if argv and argv[0] not in commands and not argv[0].startswith("-"):
            # Playground — live regex testing
            if argv[0] in ("play", "playground"):
                # Parse play-specific flags
                play_file = None
                play_regex = ""
                play_export = None
                play_output = None
                i = 1
                while i < len(argv):
                    if argv[i] == "--file" and i + 1 < len(argv):
                        play_file = argv[i + 1]
                        i += 2
                    elif argv[i] == "--regex" and i + 1 < len(argv):
                        play_regex = argv[i + 1]
                        i += 2
                    elif argv[i] == "--export" and i + 1 < len(argv):
                        play_export = argv[i + 1]
                        i += 2
                    elif argv[i] in ("-o", "--output") and i + 1 < len(argv):
                        play_output = argv[i + 1]
                        i += 2
                    elif not argv[i].startswith("-"):
                        play_regex = argv[i]
                        i += 1
                    else:
                        i += 1

                if play_file:
                    import os
                    if not os.path.isfile(play_file):
                        print(ansi.error(f"Archivo no encontrado: {play_file}"))
                        return 1

                    from pyregex.presentation.playground.core.config import PlaygroundConfig
                    pg_config = PlaygroundConfig(
                        file_export_dir=self.config.export_dir if self.config else "~/pyregex_exports"
                    )

                    # Batch export mode (no TUI)
                    if play_export and play_regex:
                        from pyregex.presentation.playground.file.reader import FileReader
                        from pyregex.presentation.playground.file.scanner import FileScanner
                        from pyregex.presentation.playground.file.exporter import (
                            FileExporter, ExportOptions,
                        )
                        reader = FileReader(play_file)
                        reader.open()
                        scanner = FileScanner(reader)
                        result = scanner.scan(play_regex)
                        exporter = FileExporter(reader)
                        output = exporter.export(
                            result,
                            ExportOptions(
                                format=play_export,
                                output_path=play_output,
                                include_groups=True,
                            ),
                        )
                        if not play_output:
                            print(output)
                        else:
                            print(ansi.success(
                                f"{result.match_count:,} matches exportados a {play_output}"
                            ))
                        reader.close()
                        return 0

                    # Interactive file mode
                    from pyregex.presentation.playground.file_app import FilePlaygroundApp
                    app = FilePlaygroundApp(
                        file_path=play_file, 
                        initial_regex=play_regex,
                        config=pg_config,
                        registry=self.registry_system,
                    )
                    app.run()
                    return 0

                # Standard sandbox mode
                from pyregex.presentation.playground.app import PlaygroundApp
                app = PlaygroundApp(initial_regex=play_regex, registry=self.registry_system)
                app.run()
                return 0

            # Route through unified Nebula engine (AHA discovery)
            from pyregex.presentation.assistant.core.oneshot import run_wizard_oneshot
            from pyregex.domain.catalog.registry import catalog_registry

            cmd = argv[0].lower()
            if cmd in catalog_registry.list_categories() or catalog_registry.get_entry(cmd):
                return run_wizard_oneshot(cmd, cli=self)

            return self.cmd_quick(" ".join(argv))

        # Standard argparse setup for commands
        parser = PyRegexParser(
            prog="px",
            description=i18n.t("cli.description"),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            add_help=True,
        )

        # Base arguments
        parser.add_argument(
            "--debug", action="store_true", help="Enable debug mode (stack traces)"
        )
        parser.add_argument("--lang", help="Set interface language (en, es)")

        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Register all modular commands
        self.dispatcher.setup_parsers(subparsers)

        try:
            args = parser.parse_args(argv)

            # Global settings
            if args.debug:
                self.config.debug = True
            if args.lang:
                i18n.init_translator(args.lang)

            # 1. Dispatch to Modular Commands
            result = self.dispatcher.dispatch(args, self)
            if result != -1:
                return result

            # 2. Dispatch to unified Nebula engine (AHA dynamic dispatch)
            from pyregex.presentation.assistant.core.oneshot import run_wizard_oneshot
            from pyregex.domain.catalog.registry import catalog_registry

            cmd = args.command
            # If it's a known category or entry, run the oneshot/wizard path
            if cmd in catalog_registry.list_categories() or catalog_registry.get_entry(cmd):
                return run_wizard_oneshot(cmd, cli=self)

            # 3. Fallback to help
            parser.print_help()
            return 1

        except (argparse.ArgumentError, SystemExit) as e:
            # Caught from PyRegexParser to prevent REPL crash
            if isinstance(e, SystemExit) and e.code == 0:
                return 0  # Help message printed successfully
            print(ansi.error(str(e)))
            return 1
        except PyRegexError as e:
            # Centralized Error Mapping (Stage 4)
            if isinstance(e, PatternNotFoundError):
                msg = "The requested pattern was not found in your library."
                if str(e):
                    msg = f"The requested pattern '{str(e)}' was not found in your library."
                print(ansi.error(msg))
            elif isinstance(e, ExecutionTimeoutError):
                msg = "Execution took too long. The pattern may be inefficient or cause ReDoS."
                print(ansi.error(msg))
            else:
                print(ansi.error(str(e)))
            return 1
        except Exception as e:
            if self.config.debug:
                import traceback

                traceback.print_exc()
            else:
                print(ansi.error(f"Unexpected Error: {str(e)}"))
            return 1

    def cmd_quick(self, intent: str) -> int:
        builder, tags = self.quick_controller.process_intent(intent)
        if not builder:
            print(ansi.error(i18n.t("common.error", message="Intent not recognized.")))
            return 1

        pattern = builder.build_pattern()

        # Record history
        self.history_repo.add(pattern, "quick")

        print(f"\n{ansi.FG_CYAN}--- Resolved Regex ---{ansi.RESET}")
        print(f"{ansi.label('Mapped Sub-program:')} {builder.__class__.__name__}")
        print(f"{ansi.label('Pattern:')} {ansi.regex_display(pattern)}")
        print(f"{ansi.label('Confidence Tags:')} {', '.join(tags)}")

        res = self.explainer.explain(pattern)
        explanation = res["narrative"] if res["success"] else [res["error"]]
        print(f"{ansi.label('Explanation:')} {', '.join(explanation)}")

        matches = builder.metadata.examples
        if matches and self.config.show_examples:
            print(f"{ansi.label('Example:')} {matches[0]}")

        print(
            f"\n{ansi.muted(f'Usage: pyregex test --pattern "{pattern}" --text "..."')}"
        )
        return 0

    def cmd_create(self, args: argparse.Namespace | None = None) -> int:
        """Detailed sub-menu for Regex creation via the Nebula Assistant Engine."""
        from pyregex.presentation.assistant.shell.repl import NebulaREPL

        repl = NebulaREPL(cli=self)
        repl.run(initial_command="create")
        return 0

    def _handle_help_flow(self, choice: str = ""):
        """Contextual and global help, utilities, and tutorials."""
        if not choice:
            choice = prompt("Help > ").strip().lower()

        if choice == "h":
            print(ansi.info(i18n.t("help_menu.help_context")))
            print(
                "Main Menu: Select a category to start building. Type 'shortcuts' for UI help."
            )
        elif choice == "hh":
            print(ansi.bold(i18n.t("help_menu.help_global")))
            modules = [
                "create",
                "test",
                "explain",
                "perf",
                "secure",
                "merge",
                "history",
                "config",
            ]
            for mod in modules:
                print(
                    f" - {ansi.label(mod)}: {i18n.t(f'cli.commands.{mod}', default=mod)}"
                )
        elif choice == "tutorial":
            print(ansi.banner(i18n.t("help_menu.tutorial")))
            for step in i18n.t("help_menu.tutorial_steps"):
                print(f" {ansi.success('→')} {step}")
                prompt("Press Enter to continue...")
        elif choice == "shortcuts":
            print(ansi.bold(i18n.t("help_menu.shortcuts")))
            for shot in i18n.t("help_menu.shortcut_list"):
                print(f" • {shot}")
        elif choice == "version":
            print(ansi.info(f"PyRegex CLI v1.0.0 (Python {sys.version.split()[0]})"))
        elif choice == "changelog":
            print(ansi.bold(i18n.t("help_menu.changelog")))
            print(i18n.t("help_menu.changelog_info"))
        elif choice == "feedback":
            print(ansi.info(i18n.t("help_menu.feedback_info")))
        elif choice == "config":
            print(ansi.bold(i18n.t("help_menu.config")))
            print(json.dumps(self.config.__dict__, indent=2))

    def _confirm_exit(self) -> bool:
        """Confirms exit if there are unsaved patterns."""
        # Simple heuristic: if we are in the middle of building but haven't saved
        confirm = prompt(i18n.t("help_menu.confirm_quit_unsaved")).strip().lower()
        return confirm == "y"
