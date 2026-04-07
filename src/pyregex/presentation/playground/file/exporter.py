"""Playground File Mode — Match Exporter.

Export regex matches to JSON, CSV, TXT (grep-style), or clipboard.
Supports context lines, group inclusion, and batch mode.
"""

from __future__ import annotations

import csv
import json
import io
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from pyregex.presentation.playground.file.scanner import ScanMatch, ScanResult
from pyregex.presentation.playground.file.reader import FileReader


@dataclass
class ExportOptions:
    """Configuration for match export."""

    format: str = "json"  # json, csv, txt, clipboard
    output_path: Optional[str] = None  # None = stdout
    include_groups: bool = True
    include_context: bool = False
    context_lines: int = 2
    include_line_numbers: bool = True
    include_header: bool = True
    pretty: bool = True  # pretty-print for JSON


class FileExporter:
    """Export scan matches in multiple formats.

    Formats:
    - **JSON**: Structured, with groups and metadata
    - **CSV**: Tabular, one match per row
    - **TXT**: grep-style output with line numbers
    - **clipboard**: Copy matching lines to system clipboard

    Usage:
        exporter = FileExporter(reader)
        output = exporter.export(scan_result, ExportOptions(format="json"))
    """

    def __init__(self, reader: Optional[FileReader] = None):
        self._reader = reader

    def export(self, result: ScanResult, options: ExportOptions) -> str:
        """Export matches according to options.

        Returns the formatted output string.
        Also writes to file if output_path is specified.
        """
        if options.format == "json":
            output = self._to_json(result, options)
        elif options.format == "csv":
            output = self._to_csv(result, options)
        elif options.format == "txt":
            output = self._to_txt(result, options)
        elif options.format == "clipboard":
            output = self._to_txt(result, options)
            self._copy_to_clipboard(output)
            return output
        else:
            raise ValueError(f"Unknown format: {options.format}")

        # Write to file if path specified
        if options.output_path:
            Path(options.output_path).write_text(output, encoding="utf-8")

        return output

    def export_lines_only(self, result: ScanResult) -> str:
        """Export just the matched lines (no decoration)."""
        seen: set[int] = set()
        lines = []
        for m in result.matches:
            if m.line_no not in seen:
                seen.add(m.line_no)
                lines.append(m.line_text)
        return "\n".join(lines)

    # ── Format: JSON ─────────────────────────────────────────────

    def _to_json(self, result: ScanResult, options: ExportOptions) -> str:
        data = {
            "metadata": {
                "pattern": result.pattern,
                "flags": result.flags,
                "total_lines": result.total_lines,
                "matched_lines": result.line_match_count,
                "total_matches": result.match_count,
                "scan_time_ms": round(result.scan_time_ms, 2),
            },
            "matches": [],
        }

        for m in result.matches:
            entry: dict = {
                "line": m.line_no,
                "text": m.match_text,
                "start": m.start,
                "end": m.end,
            }

            if options.include_groups and m.groups:
                entry["groups"] = list(m.groups)
                if m.named_groups:
                    entry["named_groups"] = m.named_groups

            if options.include_context and self._reader:
                ctx = self._reader.get_context(
                    m.line_no, before=options.context_lines, after=options.context_lines
                )
                entry["context"] = [
                    {"line": ln, "text": txt, "is_match": is_m}
                    for ln, txt, is_m in ctx
                ]

            data["matches"].append(entry)

        indent = 2 if options.pretty else None
        return json.dumps(data, indent=indent, ensure_ascii=False)

    # ── Format: CSV ──────────────────────────────────────────────

    def _to_csv(self, result: ScanResult, options: ExportOptions) -> str:
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        if options.include_header:
            headers = ["match_text", "start", "end"]
            if options.include_line_numbers:
                headers.insert(0, "line_no")
            if options.include_groups:
                # Find max group count
                max_groups = max(
                    (len(m.groups) for m in result.matches), default=0
                )
                for i in range(max_groups):
                    headers.append(f"group_{i + 1}")
            writer.writerow(headers)

        # Rows
        for m in result.matches:
            row = [m.match_text, m.start, m.end]
            if options.include_line_numbers:
                row.insert(0, m.line_no)
            if options.include_groups:
                max_g = max((len(x.groups) for x in result.matches), default=0)
                for i in range(max_g):
                    row.append(m.groups[i] if i < len(m.groups) else "")
            writer.writerow(row)

        return output.getvalue()

    # ── Format: TXT (grep-style) ─────────────────────────────────

    def _to_txt(self, result: ScanResult, options: ExportOptions) -> str:
        lines: list[str] = []

        if options.include_header:
            lines.append(f"# Pattern: {result.pattern}")
            lines.append(
                f"# {result.match_count} matches in "
                f"{result.line_match_count}/{result.total_lines} lines "
                f"({result.scan_time_ms:.1f}ms)"
            )
            lines.append("")

        seen_lines: set[int] = set()
        for m in result.matches:
            if options.include_context and self._reader and m.line_no not in seen_lines:
                seen_lines.add(m.line_no)
                ctx = self._reader.get_context(
                    m.line_no, before=options.context_lines, after=options.context_lines
                )
                for ln, txt, is_target in ctx:
                    prefix = ">" if is_target else " "
                    if options.include_line_numbers:
                        lines.append(f"{prefix}{ln:6d}: {txt}")
                    else:
                        lines.append(f"{prefix} {txt}")
                lines.append("---")
            else:
                if options.include_line_numbers:
                    lines.append(f"{m.line_no:6d}: {m.line_text}")
                else:
                    lines.append(m.line_text)

                if options.include_groups and m.groups:
                    for i, g in enumerate(m.groups):
                        if g is not None:
                            lines.append(f"        G{i + 1}: {g}")

        return "\n".join(lines)

    # ── Clipboard ────────────────────────────────────────────────

    @staticmethod
    def _copy_to_clipboard(text: str) -> None:
        """Copy text to system clipboard."""
        import subprocess
        import shutil

        for cmd in [
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
            ["wl-copy"],
            ["pbcopy"],
        ]:
            if shutil.which(cmd[0]):
                try:
                    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                    proc.communicate(text.encode())
                    if proc.returncode == 0:
                        return
                except Exception:
                    pass

        # Fallback: OSC 52 terminal escape
        import base64

        encoded = base64.b64encode(text.encode()).decode()
        print(f"\033]52;c;{encoded}\a", end="", flush=True)
