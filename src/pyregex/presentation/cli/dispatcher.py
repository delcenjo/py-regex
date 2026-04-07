from __future__ import annotations
import argparse
from typing import Dict, List, TYPE_CHECKING, Any
from pyregex.presentation.cli.base import BaseCommand

if TYPE_CHECKING:
    from pyregex.presentation.cli.cli import PyRegexCLI


class CommandDispatcher:
    """Registry and orchestrator for all modular PyRegex commands."""

    def __init__(self):
        self.commands: Dict[str, BaseCommand] = {}

    def register(self, command: BaseCommand):
        """Registers a new modular command."""
        self.commands[command.name] = command

    def setup_parsers(self, subparsers: Any):
        """Asks all registered commands to setup their CLI parsers."""
        for cmd in self.commands.values():
            cmd.setup_parser(subparsers)

    def dispatch(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        """Finds the correct command and executes its logic."""
        cmd_name = args.command
        if cmd_name in self.commands:
            return self.commands[cmd_name].execute(args, cli)

        # Fallback for old commands not yet migrated
        return -1

    def get_command_names(self) -> List[str]:
        """Returns the list of all registered command names."""
        return list(self.commands.keys())

    def get_completion_metadata(self) -> Dict[str, Any]:
        """
        Returns a dictionary structure for the shell completer.
        Format: { "cmd": ["--flag1", "--flag2"], ... }
        """
        metadata = {}
        # This is a simplified version. For nested commands,
        # we'd need a more complex extraction from argparse objects.
        # For now, we'll return the top-level commands and their basic flags.
        for name, cmd in self.commands.items():
            # In a real 'Galaxy' system, we could introspect the parser.
            # But for simplicity, we'll start with top-level name strings.
            metadata[name] = []
        return metadata
