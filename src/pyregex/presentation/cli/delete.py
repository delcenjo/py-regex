from __future__ import annotations
import argparse
from typing import TYPE_CHECKING, Any
from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi
from pyregex.infrastructure.registry.commands.delete.controller.delete_controller import (
    DeleteResolutionError,
)
from pyregex.infrastructure.registry.commands.delete.dependency.dependency_checker import (
    DependencyWarning,
)

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class DeleteCommand(BaseCommand):
    """Safely removes a pattern from the registry with dependency checking."""

    @property
    def name(self) -> str:
        return "delete"

    @property
    def help(self) -> str:
        return "Remove a pattern from the registry"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument("name", help="Name of the pattern to delete")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Delete without confirmation or dependency checks",
        )
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        target = args.name
        force = getattr(args, "force", False)

        try:
            output = cli.registry_system.delete_controller.request_delete(
                target, force=force
            )
            print(output)
            print()
            return 0

        except DeleteResolutionError as e:
            print(ansi.error(f"Pattern '{target}' not found in registry."))
            if e.suggestions:
                print(ansi.dim("\nDid you mean?"))
                for i, sugg in enumerate(e.suggestions, 1):
                    print(f"[{i}] {sugg.name}")

                resp = cli._get_arg_or_prompt(
                    None,
                    "Select a number to delete (or Enter to cancel)",
                    "delete.suggestion_prompt",
                )
                if resp and resp.isdigit() and 1 <= int(resp) <= len(e.suggestions):
                    target = e.suggestions[int(resp) - 1].name
                    return self._execute_safe_delete(target, force, cli)
            print()
            return 1

        except DependencyWarning as e:
            print(ansi.warning(f"Pattern '{target}' is currently in use by:"))
            for dep in e.dependencies:
                print(f"  - {dep}")
            print()

            resp = cli._get_arg_or_prompt(
                None,
                f"Delete '{target}' anyway and break dependencies? (y/N)",
                "delete.dependency_confirm",
            )
            if resp.lower() in ("yes", "y"):
                return self._execute_safe_delete(target, force=True, cli=cli)
            else:
                print(ansi.info("Deletion aborted."))
            return 1

        except Exception as e:
            print(ansi.error(f"Could not delete pattern: {str(e)}"))
            return 1

    def _execute_safe_delete(self, target: str, force: bool, cli: PyRegexCLI) -> int:
        if not force:
            resp = cli._get_arg_or_prompt(
                None,
                f"Are you sure you want to delete '{target}'? (y/N)",
                "delete.final_confirm",
            )
            if resp.lower() not in ("yes", "y"):
                print(ansi.info("Deletion aborted."))
                return 1

        try:
            output = cli.registry_system.delete_controller.request_delete(
                target, force=True
            )
            print(output)
            return 0
        except Exception as e:
            print(ansi.error(f"Deletion failed: {e}"))
            return 1
