import json
import re
from pathlib import Path
from typing import Iterator, Any, Optional, Callable, List

from pyregex.infrastructure.registry import registry as global_registry
from pyregex.utils import ansi

EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".idea",
    "dist",
    "build",
    "coverage",
}
EXCLUDED_EXTS = {
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".ico",
    ".svg",
    ".zip",
    ".tar",
    ".gz",
    ".pdf",
    ".mp4",
    ".obj",
    ".exe",
    ".bin",
    ".so",
    ".dll",
}


def _audit_file_worker(
    filepath: Path, rules: list[str], ignore_case: bool, registry_data: dict
) -> list[dict]:
    """Top-level worker function for multiprocessing (must be picklable)."""
    from pyregex.infrastructure.registry import PatternRegistry

    reg = PatternRegistry()
    reg.entities = registry_data.get("entities", {})
    reg.tags = registry_data.get("tags", {})

    flags = re.IGNORECASE if ignore_case else 0
    compiled = []
    for r in rules:
        resolved = reg.resolve_rule(r)
        for name, pat in resolved:
            compiled.append((name, re.compile(pat, flags)))

    results = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                for name, regex in compiled:
                    for match in regex.finditer(line):
                        val = match.group()
                        is_suspicious = False
                        if (
                            "CREDIT_CARD" in name
                            or "IBAN" in name
                            or "NIF" in name
                            or "DNI" in name
                        ):
                            from pyregex.application.services.validate.regexes import (
                                luhn_check,
                                iban_check,
                                nif_check,
                            )

                            if (
                                ("CREDIT_CARD" in name and not luhn_check(val))
                                or ("IBAN" in name and not iban_check(val))
                                or (
                                    ("NIF" in name or "DNI" in name)
                                    and not nif_check(val)
                                )
                            ):
                                is_suspicious = True

                        results.append(
                            {
                                "file": str(filepath),
                                "type": name,
                                "line": line_num,
                                "column": match.start() + 1,
                                "value": val,
                                "verified": not is_suspicious,
                            }
                        )
    except Exception as e:
        from pyregex.core.shared.exceptions import ExecutionTimeoutError

        if isinstance(e, ExecutionTimeoutError):
            raise
        pass
    return results


class AuditEngine:
    """Core engine for high-performance sensitive data scanning."""

    def __init__(self, registry=None):
        self.registry = registry or global_registry
        self._compiled_patterns: list[tuple[str, re.Pattern]] = []

    def _compile_patterns(
        self, rules: list[str], ignore_case: bool = False
    ) -> list[tuple[str, re.Pattern]]:
        """Compile regex patterns resolved through the registry."""
        flags = re.IGNORECASE if ignore_case else 0
        self._compiled_patterns = []
        for r in rules:
            resolved = self.registry.resolve_rule(r)
            for name, pat in resolved:
                self._compiled_patterns.append((name, re.compile(pat, flags)))
        return self._compiled_patterns

    def scan(
        self,
        path: str,
        rules: Optional[list[str]] = None,
        ignore_case: bool = False,
        exclude: Optional[list[str]] = None,
        max_workers: Optional[int] = None,
        progress_callback: Optional[Callable] = None,
        deep: bool = False,
    ) -> list[dict]:
        """Scans path for patterns with optional parallel processing and second-pass deep validation."""
        p = Path(path)
        exclude = exclude or []

        findings = []
        rules_list = list(rules) if rules else ["all"]
        if p.is_file():
            compiled = self._compile_patterns(rules_list, ignore_case)
            findings = self._scan_file(p, compiled)
            if deep:
                # Filter results with checksums
                findings = [f for f in findings if f.get("verified", True)]
            return findings

        if max_workers:
            from concurrent.futures import ProcessPoolExecutor
            from pyregex.application.services.execution.worker import (
                unified_worker,
                WorkerResult,
            )

            files = [
                str(f)
                for f in self._iter_files(p)
                if not (exclude and any(re.search(ex, str(f)) for ex in exclude))
            ]
            reg_data = {"entities": self.registry.entities, "tags": self.registry.tags}
            rules_list: List[str] = list(rules) if rules else ["all"]
            params = {"rules": rules_list, "ignore_case": ignore_case}

            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(unified_worker, "audit", f, params, reg_data)
                    for f in files
                ]
                for future in futures:
                    res: WorkerResult = future.result()
                    if res.success:
                        findings.extend(res.findings)
                    else:
                        print(ansi.error(f"Error auditing {res.filepath}: {res.error}"))
                    if progress_callback:
                        progress_callback()
            return findings

        # Sequential scan
        compiled = self._compile_patterns(rules_list, ignore_case)
        if p.is_dir():
            for filepath in self._iter_files(p):
                if exclude and any(re.search(ex, str(filepath)) for ex in exclude):
                    continue
                findings.extend(self._scan_file(filepath, compiled))
                if progress_callback:
                    progress_callback()
        return findings

    def scan_stream(
        self,
        path: str,
        rules: list[str],
        ignore_case: bool = False,
        exclude: Optional[list[str]] = None,
    ) -> Iterator[dict]:
        """Streaming generator: yields results one-by-one for memory-efficient large-file scanning."""
        path_obj = Path(path)
        exclude = exclude or []
        compiled_patterns = self._compile_patterns(rules, ignore_case)

        if path_obj.is_file():
            yield from self._scan_file_stream(path_obj, compiled_patterns)
        elif path_obj.is_dir():
            for filepath in self._iter_files(path_obj):
                if exclude and any(re.search(ex, str(filepath)) for ex in exclude):
                    continue
                yield from self._scan_file_stream(filepath, compiled_patterns)

    def _iter_files(self, root: Path) -> Iterator[Path]:
        """Recursively iterate standard text files, ignoring binaries and node_modules."""
        try:
            for child in root.iterdir():
                if child.is_dir():
                    if child.name not in EXCLUDED_DIRS and not child.name.startswith(
                        "."
                    ):
                        yield from self._iter_files(child)
                elif child.is_file():
                    if child.suffix not in EXCLUDED_EXTS:
                        yield child
        except PermissionError:
            pass

    def _scan_file(
        self, filepath: Path, compiled_patterns: list[tuple[str, re.Pattern]]
    ) -> list[dict]:
        """Perform high-performance regex matching on a single file line by line."""
        results = []
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    for name, regex in compiled_patterns:
                        for match in regex.finditer(line):
                            val = match.group()
                            is_suspicious = False
                            if (
                                "CREDIT_CARD" in name
                                or "IBAN" in name
                                or "NIF" in name
                                or "DNI" in name
                            ):
                                from pyregex.application.services.validate.regexes import (
                                    luhn_check,
                                    iban_check,
                                    nif_check,
                                )

                                if (
                                    ("CREDIT_CARD" in name and not luhn_check(val))
                                    or ("IBAN" in name and not iban_check(val))
                                    or (
                                        ("NIF" in name or "DNI" in name)
                                        and not nif_check(val)
                                    )
                                ):
                                    is_suspicious = True

                            results.append(
                                {
                                    "file": str(filepath),
                                    "type": name,
                                    "line": line_num,
                                    "column": match.start() + 1,
                                    "value": val,
                                    "verified": not is_suspicious,
                                }
                            )
        except Exception as e:
            from pyregex.core.shared.exceptions import ExecutionTimeoutError

            if isinstance(e, ExecutionTimeoutError):
                raise
            pass
        return results

    def _scan_file_stream(
        self, filepath: Path, compiled_patterns: list[tuple[str, re.Pattern]]
    ) -> Iterator[dict]:
        """Streaming generator variant: yields matches one-by-one without collecting in memory."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    for name, regex in compiled_patterns:
                        for match in regex.finditer(line):
                            val = match.group()
                            is_suspicious = False
                            if (
                                "CREDIT_CARD" in name
                                or "IBAN" in name
                                or "NIF" in name
                                or "DNI" in name
                            ):
                                from pyregex.application.services.validate.regexes import (
                                    luhn_check,
                                    iban_check,
                                    nif_check,
                                )

                                if (
                                    ("CREDIT_CARD" in name and not luhn_check(val))
                                    or ("IBAN" in name and not iban_check(val))
                                    or (
                                        ("NIF" in name or "DNI" in name)
                                        and not nif_check(val)
                                    )
                                ):
                                    is_suspicious = True

                            yield {
                                "file": str(filepath),
                                "type": name,
                                "line": line_num,
                                "column": match.start() + 1,
                                "value": val,
                                "verified": not is_suspicious,
                            }
        except Exception as e:
            from pyregex.core.shared.exceptions import ExecutionTimeoutError

            if isinstance(e, ExecutionTimeoutError):
                raise
            pass

    def render_detailed_report(self, results: list[dict], root_path: str = "") -> str:
        """Renders comprehensive line-by-line detailed output."""
        if not results:
            return ansi.success("AUDIT REPORT: No sensitive items detected.")

        title = (
            f"AUDIT REPORT - {Path(root_path).absolute()}"
            if root_path
            else "AUDIT REPORT"
        )
        output = [ansi.bold(title)]
        output.append("━" * 60)

        for r in results:
            t = ansi.warning(f"[{r['type']}]")
            verified_label = (
                f" {ansi.success('(Verified)')}" if r.get("verified") else ""
            )
            file_ref = ansi.dim(f"{r['file']}:{r['line']}")
            output.append(
                f"{t}{verified_label} found at {file_ref}: {ansi.regex_display(r['value'])}"
            )

        output.append("━" * 60)
        output.append(ansi.error(f"{len(results)} SENSITIVE ITEMS DETECTED"))
        return "\n".join(output)

    def render_summary_table(self, results: list[dict]) -> str:
        """Renders an aggregated ASCII summary table."""
        if not results:
            return ansi.success("SUMMARY: 0 sensitive items found.")

        summary: dict[str, dict[str, Any]] = {}
        for r in results:
            t = r["type"]
            if t not in summary:
                summary[t] = {"matches": 0, "lines": set()}
            summary[t]["matches"] += 1
            summary[t]["lines"].add(r["line"])

        output = [ansi.error(f"SUMMARY: {len(results)} sensitive items found")]
        output.append("┌" + "─" * 17 + "┬" + "─" * 10 + "┬" + "─" * 15 + "┐")
        output.append(
            f"│ {ansi.bold('Type'.ljust(15))} │ {ansi.bold('Matches'.ljust(8))} │ {ansi.bold('Lines'.ljust(13))} │"
        )
        output.append("├" + "─" * 17 + "┼" + "─" * 10 + "┼" + "─" * 15 + "┤")

        for t, data in summary.items():
            lines_set = data["lines"]
            sorted_lines = sorted(list(lines_set))
            top_lines = []
            for i, line_num in enumerate(sorted_lines):
                if i >= 3:
                    break
                top_lines.append(str(line_num))
            lines_str = ",".join(top_lines)
            if len(lines_set) > 3:
                lines_str += ",..."
            output.append(f"│ {t:<15} │ {str(data['matches']):<8} │ {lines_str:<13} │")

        output.append("└" + "─" * 17 + "┴" + "─" * 10 + "┴" + "─" * 15 + "┘")
        return "\n".join(output)

    def render_json(self, results: list[dict], root_path: str = "") -> str:
        """Outputs standard JSON array object suitable for CI/CD integration."""
        return json.dumps(
            {
                "target": str(Path(root_path).absolute()) if root_path else "",
                "total_findings": len(results),
                "findings": results,
            },
            indent=2,
        )
