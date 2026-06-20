import json

from pyregex.utils import ansi
from pyregex.application.services.validate.engine import ValidationResult


def render_detailed_report(result: ValidationResult) -> str:
    """Renders a full ANSI-colored validation report."""
    lines = []
    title = f"VALIDATION REPORT - {result.source}"
    lines.append(ansi.bold(title))
    lines.append("━" * 60)

    pct = result.percentage
    color_fn = (
        ansi.success if pct >= 90 else (ansi.warning if pct >= 50 else ansi.error)
    )
    lines.append(
        color_fn(
            f"{result.valid}/{result.total} {result.type_name} válidos ({pct:.1f}%)"
        )
    )

    if result.errors:
        lines.append("")
        lines.append(ansi.error(f"{len(result.errors)} errores encontrados:"))
        lines.append("")
        for err in result.errors:
            loc = f"Línea {err.line}"
            if err.column > 0:
                loc += f", col {err.column}"
            val_display = ansi.regex_display(err.value[:40])
            lines.append(f"  {ansi.warning(loc)}: {val_display} → {err.reason}")

    lines.append("━" * 60)
    return "\n".join(lines)


def render_summary(result: ValidationResult) -> str:
    """One-line summary."""
    pct = result.percentage
    status = "" if pct == 100 else "" if pct >= 50 else ""
    return f"{status} {result.valid}/{result.total} {result.type_name} válidos ({pct:.1f}%) en {result.source}"


def render_json(result: ValidationResult) -> str:
    """Structured JSON for CI/CD."""
    return json.dumps(
        {
            "source": result.source,
            "type": result.type_name,
            "total": result.total,
            "valid": result.valid,
            "invalid": result.invalid,
            "percentage": round(result.percentage, 2),
            "errors": [
                {
                    "line": e.line,
                    "column": e.column,
                    "value": e.value,
                    "reason": e.reason,
                }
                for e in result.errors
            ],
        },
        indent=2,
        ensure_ascii=False,
    )
