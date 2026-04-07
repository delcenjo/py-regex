# src/pyregex/domain/explain/engine.py
from __future__ import annotations
from typing import Dict, Any

from pyregex.domain.explain.lexer.scanner import Scanner
from pyregex.domain.explain.parser.recursive_descent import RecursiveDescentParser
from pyregex.domain.explain.analyzer.complexity import ComplexityAnalyzer
from pyregex.domain.explain.analyzer.linter import AstLinter
from pyregex.domain.explain.formatters.tree import TreeFormatter
from pyregex.domain.explain.formatters.mermaid import MermaidFormatter
from pyregex.domain.explain.translator.ast_walker import NarrativeTranslator
from pyregex.domain.explain.redos import ReDoSAnalyzer
import logging

logger = logging.getLogger(__name__)


class AdvancedExplainer:
    """The central compiler facade orchestrating the complete Regex Analysis Pipeline."""

    def explain(self, pattern: str) -> Dict[str, Any]:
        """Compiles a regex string, returning deep intelligence and visual representations."""
        try:
            tokens = Scanner(pattern).scan()
            ast = RecursiveDescentParser(tokens).parse()

            comp_score, comp_warns = ComplexityAnalyzer(ast).analyze()
            lint_sugs = AstLinter(ast).lint()

            tree_str = TreeFormatter(ast).format()
            mermaid_str = MermaidFormatter(ast).format()
            narrative = NarrativeTranslator(ast).translate()

            # ReDoS Analysis (deterministic)
            try:
                redos_report = ReDoSAnalyzer().analyze(pattern)
                redos_data = redos_report.to_dict()
                # Upgrade complexity with ReDoS engine result
                if redos_report.complexity.notation != "O(N)":
                    comp_score = redos_report.complexity.notation
            except Exception as e:
                logger.warning("ReDoS analysis failed in explain engine %s", e, exc_info=True)
                redos_data = {}

            return {
                "success": True,
                "pattern": pattern,
                "complexity": comp_score,
                "warnings": comp_warns,
                "suggestions": lint_sugs,
                "tree": tree_str,
                "mermaid": mermaid_str,
                "narrative": narrative,
                "redos": redos_data,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "narrative": [f"Error de análisis sintáctico: {str(e)}"],
            }
