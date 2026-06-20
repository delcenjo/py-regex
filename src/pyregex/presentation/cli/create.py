from __future__ import annotations
import argparse
from typing import Any
from pyregex.presentation.cli.base import BaseCommand
from pyregex.i18n import translator as i18n


class CreateCommand(BaseCommand):
    """Modular command for initiating the creation assistant."""

    @property
    def name(self) -> str:
        return "create"

    @property
    def description(self) -> str:
        return (
            i18n.t("cli.commands.create")
            or "Create new regular expression patterns interactively."
        )

    @property
    def help(self) -> str:
        return self.description

    def setup_parser(self, subparsers: Any) -> None:
        """Sets up the subparser for the create command."""
        parser = subparsers.add_parser(self.name, help=self.description)

    def execute(self, args: argparse.Namespace, cli: Any) -> int:
        """Executes the create component via the primary CLI assistant."""
        return cli.cmd_create(args)
