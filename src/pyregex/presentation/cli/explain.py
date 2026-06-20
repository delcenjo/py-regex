# src/pyregex/presentation/cli/explain.py
from __future__ import annotations
import argparse
from typing import TYPE_CHECKING, Any
from pyregex.presentation.cli.base import BaseCommand
from pyregex.utils import ansi
from pyregex.domain.explain.engine import AdvancedExplainer

if TYPE_CHECKING:
    from pyregex.presentation.cli.cli import PyRegexCLI


class ExplainCommand(BaseCommand):
    """Generates a deep Compiler-level analysis and explanation of a regex pattern."""

    @property
    def name(self) -> str:
        return "explain"

    @property
    def help(self) -> str:
        return "Recibe análisis estructural, léxico y de seguridad (AST) de una Regex"

    def setup_parser(self, subparsers: Any) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(self.name, help=self.help)
        parser.add_argument("pattern", type=str, help="Patrón regex a explicar")
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Muestra gráficos AST, puntaje Big-O, y sugerencias completas",
        )
        parser.add_argument(
            "--mermaid",
            action="store_true",
            help="Exporta la estructura de la Regex en un gráfico de estados Mermaid",
        )
        return parser

    def execute(self, args: argparse.Namespace, cli: PyRegexCLI) -> int:
        cli.history_repo.add(args.pattern, "explain")

        engine = AdvancedExplainer()
        result = engine.explain(args.pattern)

        if not result.get("success"):
            print(f"{ansi.error('Error Crítico:')} {result['narrative'][0]}")
            return 1

        print(f"\n{ansi.bold('PATRÓN REGEX:')} {ansi.regex_display(args.pattern)}\n")

        # 1. Natural Language Representation
        print(f"{ansi.FG_CYAN}--- TRADUCCIÓN SEMÁNTICA ---{ansi.RESET}")
        for n in result["narrative"]:
            print(f" {ansi.success('✓')} {n}")

        # 2. Advanced Output (Tree + Metrics)
        if args.verbose:
            print(f"\n{ansi.FG_CYAN}--- ANÁLISIS DE COMPLEJIDAD ---{ansi.RESET}")

            c_score = result["complexity"]
            c_color = ansi.error if c_score == "O(2^N)" else ansi.success

            print(f" * Orden Estructural: {c_color(c_score)}")

            for w in result["warnings"]:
                print(f" * {ansi.error('Advertencia de Rendimiento:')} {w}")
            for s in result["suggestions"]:
                print(f" * {ansi.warning('Sugerencias de Linting:')} {s['message']}")

            print(
                f"\n{ansi.FG_CYAN}--- ÁRBOL DE SINTAXIS ABSTRACTA (AST) ---{ansi.RESET}"
            )
            print(result["tree"])

        # 3. Mermaid Graph
        if args.mermaid:
            print(f"\n{ansi.FG_CYAN}--- GRÁFICO DE ESTADOS (MERMAID) ---{ansi.RESET}")
            print(result["mermaid"])

        return 0
