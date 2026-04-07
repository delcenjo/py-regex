from __future__ import annotations
import re
import sys
import time
from pathlib import Path
from typing import Optional, Callable

from pyregex.application.services.audit.engine import AuditEngine
from pyregex.infrastructure.registry import registry as global_registry
from pyregex.application.services.mask.modes import MODES
from pyregex.utils import ansi


# Files larger than this threshold (bytes) trigger progress reporting
LARGE_FILE_THRESHOLD = 5 * 1024 * 1024  # 5 MB


class MaskEngine:
    """Core engine for intelligently anonymizing sensitive data in files and streams.

    Uses streaming line-by-line processing to handle arbitrarily large files
    without loading them entirely into memory.
    """

    def __init__(self, mode: str = "redact", salt: str = "pyregex2026", registry=None):
        self.mode = mode
        self.salt = salt
        self.registry = registry or global_registry
        self.audit_engine = AuditEngine(registry=self.registry)
        self.mask_func = MODES.get(mode, MODES["redact"])
        self._compiled_patterns: list[tuple[str, re.Pattern]] = []

    def _compile_patterns(
        self, rules: list[str], ignore_case: bool = False
    ) -> list[tuple[str, re.Pattern]]:
        """Compile patterns resolved through the registry."""
        flags = re.IGNORECASE if ignore_case else 0
        self._compiled_patterns = []
        for r in rules:
            resolved = self.registry.resolve_rule(r)
            for name, pat in resolved:
                self._compiled_patterns.append((name, re.compile(pat, flags)))
        return self._compiled_patterns

    def _mask_line(
        self, line: str, compiled_patterns: list[tuple[str, re.Pattern]]
    ) -> tuple[str, int]:
        """Masks a single line, resolving overlapping matches. O(n) memory per line."""
        matches = []
        for name, regex in compiled_patterns:
            for m in regex.finditer(line):
                matches.append((m.start(), m.end(), name, m.group()))

        if not matches:
            return line, 0

        # Sort by position, longest match first to avoid subset corruption
        matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

        filtered = []
        last_end = -1
        for m in matches:
            start, end, name, value = m
            if start >= last_end:
                filtered.append(m)
                last_end = end

        parts = []
        last_idx = 0
        for start, end, name, value in filtered:
            parts.append(line[last_idx:start])
            parts.append(self.mask_func(value, self.salt, name))
            last_idx = end
        parts.append(line[last_idx:])

        return "".join(parts), len(filtered)

    def mask_string(
        self, content: str, rules: list[str], ignore_case: bool = False
    ) -> tuple[str, int]:
        """Anonymizes all found sensitive elements in a string."""
        compiled = self._compile_patterns(rules, ignore_case)
        total_count = 0
        result_lines = []
        for line in content.splitlines(keepends=True):
            masked, count = self._mask_line(line, compiled)
            result_lines.append(masked)
            total_count += count
        return "".join(result_lines), total_count

    def mask_file(
        self,
        filepath: str,
        rules: list[str],
        output_path: Optional[str] = None,
        inplace: bool = False,
        dry_run: bool = False,
        ignore_case: bool = False,
    ) -> int:
        """Processes a single file using streaming line-by-line to support large files."""
        path = Path(filepath)
        compiled = self._compile_patterns(rules, ignore_case)

        try:
            file_size = path.stat().st_size
        except OSError:
            return 0

        is_large = file_size > LARGE_FILE_THRESHOLD
        total_count = 0

        if dry_run:
            # Dry-run: just count matches line by line, no writes
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        _, count = self._mask_line(line, compiled)
                        total_count += count
            except Exception:
                return 0

            if total_count > 0:
                print(f"✅ {ansi.warning('Would mask')} {total_count} items in {path}")
            return total_count

        if inplace or output_path:
            # Streaming write: read line by line, write to temp/output, then swap if in-place
            import tempfile

            out_path = Path(output_path) if output_path else None
            if out_path:
                out_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                # Write to temp file first (safe for in-place)
                dest = out_path or Path(
                    tempfile.mktemp(suffix=path.suffix, dir=path.parent)
                )
                bytes_processed = 0
                t0 = time.monotonic()

                with (
                    open(path, "r", encoding="utf-8", errors="ignore") as fin,
                    open(dest, "w", encoding="utf-8") as fout,
                ):
                    for line in fin:
                        masked, count = self._mask_line(line, compiled)
                        fout.write(masked)
                        total_count += count
                        bytes_processed += len(line.encode("utf-8"))

                        # Progress reporting for large files
                        if is_large and bytes_processed % (1024 * 1024) < len(
                            line.encode("utf-8")
                        ):
                            pct = min(100, int(bytes_processed / file_size * 100))
                            elapsed = time.monotonic() - t0
                            sys.stderr.write(
                                f"\r⏳ Processing {path.name}... {pct}% ({elapsed:.1f}s)"
                            )
                            sys.stderr.flush()

                if is_large:
                    elapsed = time.monotonic() - t0
                    sys.stderr.write(
                        f"\r✅ Processed {path.name} in {elapsed:.1f}s              \n"
                    )
                    sys.stderr.flush()

                # If in-place and we wrote to a temp file, swap
                if inplace and not output_path:
                    import shutil

                    shutil.move(str(dest), str(path))

                if total_count > 0:
                    target = path if inplace else dest
                    label = "(in-place)" if inplace else ""
                    print(
                        f"✅ {ansi.success('Masked')} {total_count} items → {target} {label}"
                    )

            except Exception:
                return 0
        else:
            # Stdout streaming: write masked lines directly to stdout
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        masked, count = self._mask_line(line, compiled)
                        sys.stdout.write(masked)
                        total_count += count
            except Exception:
                return 0

        return total_count

    def mask_directory(
        self,
        dirpath: str,
        rules: list[str],
        output_dir: Optional[str] = None,
        inplace: bool = False,
        dry_run: bool = False,
        ignore_case: bool = False,
        exclude: Optional[list[str]] = None,
        max_workers: Optional[int] = None,
        progress_callback: Optional[Callable[[str], None]] = None,
        skip_files: Optional[list[str]] = None,
    ) -> tuple[int, int]:
        """Recursively walks a directory performing masks with pattern caching and optional parallelism and skip list."""
        total_masked = 0
        files_modified = 0
        root = Path(dirpath)
        exclude = exclude or []

        if max_workers and not dry_run and not output_dir:
            from concurrent.futures import ProcessPoolExecutor, as_completed
            from pyregex.application.services.execution.worker import (
                unified_worker,
                WorkerResult,
            )

            files = [
                str(f)
                for f in self.audit_engine._iter_files(root)
                if not (exclude and any(re.search(ex, str(f)) for ex in exclude))
            ]
            if skip_files:
                files = [f for f in files if f not in skip_files]

            reg_data = {"entities": self.registry.entities, "tags": self.registry.tags}
            params = {
                "rules": rules,
                "mode": self.mode,
                "salt": self.salt,
                "inplace": inplace,
                "ignore_case": ignore_case,
            }

            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(unified_worker, "mask", f, params, reg_data)
                    for f in files
                ]
                for future in as_completed(futures):
                    res: WorkerResult = future.result()
                    if res.success:
                        if res.items_count > 0:
                            total_masked += res.items_count
                            files_modified += 1
                    else:
                        from pyregex.utils import ansi

                        print(ansi.error(f"Error masking {res.filepath}: {res.error}"))
                    if progress_callback:
                        progress_callback(res.filepath)
            return total_masked, files_modified

        # Pre-compile patterns once for the entire directory scan
        self._compile_patterns(rules, ignore_case)

        for filepath in self.audit_engine._iter_files(root):
            if exclude and any(re.search(ex, str(filepath)) for ex in exclude):
                continue
            if skip_files and str(filepath) in skip_files:
                continue

            rel_path = filepath.relative_to(root)

            if output_dir:
                out_p = Path(output_dir) / rel_path
                count = self.mask_file(
                    str(filepath),
                    rules,
                    output_path=str(out_p),
                    dry_run=dry_run,
                    ignore_case=ignore_case,
                )
            else:
                count = self.mask_file(
                    str(filepath),
                    rules,
                    inplace=inplace,
                    dry_run=dry_run,
                    ignore_case=ignore_case,
                )

            if count > 0:
                total_masked += count
                files_modified += 1
            if progress_callback:
                progress_callback(str(filepath))

        return total_masked, files_modified
