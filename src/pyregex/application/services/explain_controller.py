from __future__ import annotations
from pyregex.domain.explain.parser.regex_parser import RegexParser
from pyregex.domain.explain.analyzer.semantic_analyzer import SemanticAnalyzer
from pyregex.domain.explain.simplifier.ast_simplifier import ASTSimplifier
from pyregex.domain.explain.patterns.recognizer import PatternRecognizer
from pyregex.domain.explain.warnings.linter import WarningLinter
from pyregex.domain.explain.translator.human_translator import HumanTranslator
from pyregex.domain.explain.output.formatter import ExplainFormatter


class ExplainController:
    """Orchestrates the complete Explain pipeline execution."""

    def __init__(self):
        self.analyzer = SemanticAnalyzer()
        self.simplifier = ASTSimplifier()
        self.recognizer = PatternRecognizer()
        self.linter = WarningLinter()
        self.formatter = ExplainFormatter()

    def explain(self, pattern: str, mode: str = "detailed") -> str:
        # 1. Parse -> AST
        try:
            parser = RegexParser(pattern)
            ast_root = parser.parse()
        except Exception as e:
            return f"Error parsing regex: {e}"

        # 2. Semantic Analysis
        metrics = self.analyzer.analyze(ast_root)

        # 3. Macro Pattern Recognition
        tags = self.recognizer.recognize(ast_root)

        # 4. Lint Warnings
        warnings = self.linter.lint(ast_root)

        # 5. Simplify AST
        simplified_ast = self.simplifier.simplify(ast_root)

        # 6. Translate to Human
        translator = HumanTranslator(mode)
        translation = translator.translate(simplified_ast)

        # 7. Format Output
        return self.formatter.format_output(
            mode=mode,
            pattern=pattern,
            translation=translation,
            tags=tags,
            metrics=metrics,
            warnings=warnings,
        )
