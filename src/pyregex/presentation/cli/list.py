from __future__ import annotations
import argparse
from typing import TYPE_CHECKING, Any
from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi
from pyregex.infrastructure.registry.commands.list.query.builder import QueryBuilder

if TYPE_CHECKING:
    from pyregex.cli import PyRegexCLI


class ListCommand(BaseCommand):
    """Lists and discovers saved patterns in the registry."""

    @property
    def name(self) -> str:
        return "list"

    @property
    def help(self) -> str:
        return "List and discover saved patterns"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument("--tag", help="Filter by tag")
        parser.add_argument("--category", help="Filter by category")
        parser.add_argument("--search", help="Search by name or description")
        parser.add_argument(
            "--sort",
            default="name",
            choices=["name", "date", "usage"],
            help="Sort field",
        )
        parser.add_argument(
            "--group",
            choices=["category", "tag", "none"],
            help="Group results by field",
        )
        parser.add_argument(
            "--view",
            default="simple",
            choices=["simple", "detailed", "compact"],
            help="Display mode",
        )
        parser.add_argument("--page", type=int, default=1, help="Page number")
        parser.add_argument("--limit", type=int, default=50, help="Results per page")
        parser.add_argument(
            "--scope",
            choices=["private", "global", "all"],
            default="all",
            help="Registry scope",
        )
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        ansi.print_banner("Registry Discovery")

        qb = QueryBuilder()
        qb.with_keyword(getattr(args, "search", None))
        qb.with_tag(getattr(args, "tag", None))
        qb.with_category(getattr(args, "category", None))

        sort_by = getattr(args, "sort", "name")
        qb.sort_by(sort_by)

        group_by = getattr(args, "group", None)
        qb.group_by(group_by)

        view_mode = getattr(args, "view", "simple")
        qb.view_as(view_mode)

        qb.paginate(page=getattr(args, "page", 1), limit=getattr(args, "limit", 50))

        query = qb.build()
        output = cli.registry_system.list(query)
        print(output)
        print()
        return 0
