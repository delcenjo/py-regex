"""ReDoS Engine — Deterministic regex vulnerability analysis.

Public API for the ReDoS detection system. Orchestrates:
1. AST parsing (via existing Scanner + RecursiveDescentParser)
2. NFA construction (Thompson algorithm)
3. NFA simulation (ambiguity detection)
4. Static analysis (overlap, quantifier chains, anchor protection)
5. Complexity calculation (Big-O classification)
6. Safe rewriting (automatic fix suggestions)
7. Dynamic testing (NFA-guided pump generation)
"""

from __future__ import annotations
from typing import Optional
import logging

logger = logging.getLogger(__name__)

from pyregex.domain.explain.redos.models import (
    ReDoSReport,
    Vulnerability,
    ComplexityResult,
    Severity,
)


class ReDoSAnalyzer:
    """Public facade for deterministic ReDoS detection.

    Unlike LLMs, this analyzer:
    - Builds an NFA from the regex AST and simulates paths
    - Computes exact character set overlaps via 256-bit bitsets
    - Classifies complexity as O(N), O(N²), O(N³), or O(2^N)
    - Generates deterministic evil inputs from NFA pump paths
    - Suggests safe rewrites that compile correctly
    """

    def __init__(self, dynamic_timeout_ms: int = 2000):
        self._dynamic_timeout_ms = dynamic_timeout_ms

    def analyze(self, pattern: str) -> ReDoSReport:
        """Full ReDoS analysis pipeline.

        Pipeline: parse → NFA → simulate → overlap → chains →
                  anchors → complexity → rewrite → pump
        """
        if not pattern or not pattern.strip():
            return ReDoSReport(pattern=pattern)

        # 1. Parse AST
        ast = self._parse(pattern)
        if ast is None:
            return ReDoSReport(pattern=pattern)

        vulnerabilities: list[Vulnerability] = []

        # 2. Build NFA
        nfa_complexity = "O(N)"
        nfa_state_count = 0
        pump_path = None
        try:
            from pyregex.domain.explain.redos.nfa.builder import NFABuilder
            from pyregex.domain.explain.redos.nfa.simulator import NFASimulator

            builder = NFABuilder()
            start, accept, state_count = builder.build(ast)
            nfa_state_count = state_count

            # 3. NFA simulation — find ambiguities
            sim = NFASimulator(start, accept)
            ambiguities = sim.find_ambiguities()
            nfa_complexity = sim.classify_ambiguity(ambiguities)

            # Build pump path from worst ambiguity
            if ambiguities:
                worst = max(ambiguities, key=lambda a: a.loop_depth)
                pump_path = sim.trace_pump(worst)
        except Exception as e:
            logger.debug("NFA analysis failed %s", e, exc_info=True)

        # 4. Static analysis — overlap detection
        try:
            from pyregex.domain.explain.redos.analysis.overlap import OverlapAnalyzer

            vulnerabilities.extend(OverlapAnalyzer().analyze(ast))
        except Exception as e:
            logger.debug("Overlap analysis failed %s", e)

        # 5. Quantifier chain analysis
        try:
            from pyregex.domain.explain.redos.analysis.quantifier_chain import (
                QuantifierChainAnalyzer,
            )

            vulnerabilities.extend(QuantifierChainAnalyzer().analyze(ast))
        except Exception as e:
            logger.debug("Quantifier chain analysis failed %s", e)

        # 6. Anchor protection check
        anchor_protected = False
        try:
            from pyregex.domain.explain.redos.analysis.anchor_checker import (
                AnchorChecker,
            )

            checker = AnchorChecker()
            _, _, fully = checker.check(ast)
            anchor_protected = fully
            if fully:
                vulnerabilities = checker.mitigate(vulnerabilities, ast)
        except Exception as e:
            logger.debug("Anchor protection check failed %s", e)

        # 7. Complexity calculation
        try:
            from pyregex.domain.explain.redos.analysis.complexity_calc import (
                ComplexityCalculator,
            )

            complexity = ComplexityCalculator().calculate(
                vulnerabilities, anchor_protected, nfa_complexity
            )
        except Exception as e:
            logger.debug("Complexity calculation failed %s", e)
            complexity = ComplexityResult()

        # 8. Safe rewrite
        safe_rewrite = None
        try:
            from pyregex.domain.explain.redos.rewriter.engine import RewriteEngine

            result = RewriteEngine().rewrite(pattern, ast, vulnerabilities)
            if result:
                safe_rewrite = result.rewritten
        except Exception as e:
            logger.debug("Rewrite engine failed %s", e)

        # 9. Evil input generation
        evil_input = None
        pump_char = None
        if pump_path and pump_path.pump:
            try:
                from pyregex.domain.explain.redos.dynamic.pump_generator import (
                    PumpGenerator,
                )

                gen = PumpGenerator(timeout_ms=self._dynamic_timeout_ms)
                evil_input = gen.generate_evil(pump_path)
                pump_char = pump_path.pump
            except Exception as e:
                logger.debug("Evil input generation failed %s", e)

        return ReDoSReport(
            pattern=pattern,
            vulnerabilities=vulnerabilities,
            complexity=complexity,
            evil_input=evil_input,
            pump_char=pump_char,
            safe_rewrite=safe_rewrite,
            nfa_state_count=nfa_state_count,
        )

    def quick_check(self, pattern: str) -> str:
        """Quick risk level check. Returns severity as string."""
        report = self.analyze(pattern)
        return report.risk_level.value

    def suggest_fix(self, pattern: str) -> Optional[str]:
        """Returns safe rewrite or None."""
        report = self.analyze(pattern)
        return report.safe_rewrite

    def _parse(self, pattern: str):
        """Parse regex pattern to AST using existing infrastructure."""
        try:
            from pyregex.domain.explain.lexer.scanner import Scanner
            from pyregex.domain.explain.parser.recursive_descent import (
                RecursiveDescentParser,
            )

            tokens = Scanner(pattern).scan()
            return RecursiveDescentParser(tokens).parse()
        except Exception:
            return None
