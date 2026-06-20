from __future__ import annotations
from abc import ABC, abstractmethod
import argparse
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class BaseCommand(ABC):
    """Abstract base class for all PyRegex CLI commands."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The command name (e.g., 'test', 'run')."""
        pass

    @property
    @abstractmethod
    def help(self) -> str:
        """Brief help description for the command."""
        pass

    @abstractmethod
    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        """Configures the argparse subparser for this command."""
        pass

    @abstractmethod
    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        """Executes the command logic."""
        pass
