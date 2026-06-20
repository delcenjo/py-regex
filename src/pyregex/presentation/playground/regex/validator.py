"""Playground — Live Validator.

Validates regex patterns as you type with error position highlighting.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import re


@dataclass
class ValidationIssue:
    """A validation issue with position info."""

    message: str
    position: Optional[int] = None
    severity: str = "error"  # error, warning, info
    span: Optional[tuple[int, int]] = None

    @property
    def icon(self) -> str:
        icons = {"error": "❌", "warning": "⚠️", "info": "💡"}
        return icons.get(self.severity, "❓")


@dataclass
class ValidationResult:
    """Complete validation result."""

    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    group_count: int = 0
    named_groups: list[str] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)


class LiveValidator:
    """
    Validates regex in real-time as the user types.

    Provides:
    - Syntax validation with error positions
    - Balance checking (parentheses, brackets)
    - Common mistake detection
    - Partial validation (for incomplete patterns)
    """

    def validate(self, pattern: str, flags: int = 0) -> ValidationResult:
        """Full validation of a regex pattern."""
        if not pattern:
            return ValidationResult(is_valid=True)

        issues: list[ValidationIssue] = []

        # 1. Try to compile
        try:
            compiled = re.compile(pattern, flags)
            group_count = compiled.groups
            named = list(compiled.groupindex.keys())
        except re.error as e:
            pos = getattr(e, "pos", None)
            span = (
                (max(0, pos - 1), min(len(pattern), pos + 2))
                if pos is not None
                else None
            )
            issues.append(
                ValidationIssue(
                    message=str(e),
                    position=pos,
                    severity="error",
                    span=span,
                )
            )
            return ValidationResult(is_valid=False, issues=issues)

        # 2. Balance checks
        issues.extend(self._check_balance(pattern))

        # 3. Redundancy checks
        issues.extend(self._check_redundancy(pattern))

        # 4. Common mistakes
        issues.extend(self._check_common_mistakes(pattern))

        return ValidationResult(
            is_valid=True,
            issues=issues,
            group_count=group_count,
            named_groups=named,
        )

    def validate_partial(self, pattern: str) -> ValidationResult:
        """
        Validate a partially typed pattern.
        More lenient — doesn't flag unclosed groups at the end.
        """
        if not pattern:
            return ValidationResult(is_valid=True)

        # Try compiling but don't error on unclosed groups at end
        try:
            re.compile(pattern)
            return self.validate(pattern)
        except re.error as e:
            err_str = str(e).lower()
            # These are expected for incomplete patterns
            if any(
                x in err_str
                for x in [
                    "unterminated",
                    "missing )",
                    "missing ]",
                    "unbalanced parenthesis",
                    "nothing to repeat",
                ]
            ):
                return ValidationResult(
                    is_valid=False,
                    issues=[
                        ValidationIssue(
                            message="Patrón incompleto...",
                            severity="info",
                        )
                    ],
                )
            # Real errors
            pos = getattr(e, "pos", None)
            return ValidationResult(
                is_valid=False,
                issues=[
                    ValidationIssue(
                        message=str(e),
                        position=pos,
                        severity="error",
                    )
                ],
            )

    def _check_balance(self, pattern: str) -> list[ValidationIssue]:
        issues = []
        paren_depth = 0
        bracket_depth = 0
        i = 0

        while i < len(pattern):
            ch = pattern[i]
            if ch == "\\" and i + 1 < len(pattern):
                i += 2
                continue

            if bracket_depth > 0:
                if ch == "]":
                    bracket_depth -= 1
                i += 1
                continue

            if ch == "[":
                bracket_depth += 1
            elif ch == "]" and bracket_depth == 0:
                issues.append(
                    ValidationIssue(
                        message="']' sin '[' correspondiente",
                        position=i,
                        severity="warning",
                    )
                )
            elif ch == "(":
                paren_depth += 1
            elif ch == ")":
                if paren_depth == 0:
                    issues.append(
                        ValidationIssue(
                            message="')' sin '(' correspondiente",
                            position=i,
                            severity="error",
                        )
                    )
                else:
                    paren_depth -= 1
            i += 1

        return issues

    def _check_redundancy(self, pattern: str) -> list[ValidationIssue]:
        issues = []

        # [a] → a
        for m in re.finditer(r"\[([^\]\\])\]", pattern):
            if m.group(1) not in "^-":
                issues.append(
                    ValidationIssue(
                        message=f"[{m.group(1)}] se puede simplificar a {m.group(1)}",
                        position=m.start(),
                        severity="info",
                    )
                )

        # (?:a) → a  (single char in non-capturing group)
        for m in re.finditer(r"\(\?:([^\)\\])\)", pattern):
            issues.append(
                ValidationIssue(
                    message=f"(?:{m.group(1)}) innecesario — usar {m.group(1)}",
                    position=m.start(),
                    severity="info",
                )
            )

        return issues

    def _check_common_mistakes(self, pattern: str) -> list[ValidationIssue]:
        issues = []

        # Unescaped special characters that might be intended as literal
        for m in re.finditer(r"(?<!\\)\.", pattern):
            # Skip if followed by quantifier (intended as regex dot)
            if m.end() < len(pattern) and pattern[m.end()] in "+*?{":
                continue
            # Check context — if surrounded by literals, probably a mistake
            ctx = pattern[max(0, m.start() - 1) : min(len(pattern), m.end() + 1)]
            if re.match(r"[a-zA-Z]\.[a-zA-Z]", ctx):
                issues.append(
                    ValidationIssue(
                        message=f"'.' sin escapar en pos {m.start()} — ¿debería ser '\\.'?",
                        position=m.start(),
                        severity="info",
                    )
                )

        return issues

    def format_issues(self, result: ValidationResult) -> list[str]:
        """Format validation issues for display."""
        if not result.issues:
            return ["  ✅ Patrón válido"]

        lines = []
        for issue in result.issues:
            pos_str = f" (pos {issue.position})" if issue.position is not None else ""
            lines.append(f"  {issue.icon} {issue.message}{pos_str}")
        return lines
