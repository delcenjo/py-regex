from typing import Dict, List, Optional
from pathlib import Path
import re
import os
from pyregex.application.services.mask.engine import MaskEngine
from pyregex.infrastructure.registry import registry as global_registry


class TransformEngine:
    """Core engine for complex multi-rule data pipelines.

    Allows chaining multiple transformation rules (mask, hash, redact, drop)
    in a single pass over a stream of data.
    """

    def __init__(self, rules: Dict[str, str], registry=None):
        self.registry = registry or global_registry
        self.mask_engine = MaskEngine(registry=self.registry)
        self.rules = (
            rules  # Dict mapping entity_name/regex -> action (mask, hash, redact, drop)
        )
        self.compiled_rules: List[tuple[str, re.Pattern, str]] = []
        self._compile_rules()

    def _compile_rules(self):
        """Compiles all rules into a list of (name, pattern, action)."""
        self.compiled_rules = []
        for r_input, action in self.rules.items():
            resolved = self.registry.resolve_rule(r_input)
            for name, pattern_str in resolved:
                self.compiled_rules.append((name, re.compile(pattern_str), action))

    def transform_file(
        self, source: Path, destination: Optional[Path] = None, inplace: bool = False
    ) -> int:
        """Streams a file and applies all transformation rules in a single pass."""
        source = Path(source)
        target = Path(destination) if destination else source

        if not destination and not inplace:
            # Stream to stdout
            total_count = 0
            with open(source, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    masked, count = self._transform_line(line)
                    import sys

                    sys.stdout.write(masked)
                    total_count += count
            return total_count

        import tempfile
        import shutil

        fd, temp_path = tempfile.mkstemp(dir=source.parent)
        try:
            total_count = 0
            with os.fdopen(fd, "w", encoding="utf-8") as tmp:
                with open(source, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        masked, count = self._transform_line(line)
                        tmp.write(masked)
                        total_count += count

            shutil.move(temp_path, target)
            return total_count
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise e

    def transform_directory(
        self,
        dirpath: str,
        pipeline: List[tuple[str, str]],
        output_dir: Optional[str] = None,
        max_workers: Optional[int] = None,
        progress_callback=None,
    ) -> tuple[int, int]:
        """Recursively transforms all files in a directory."""
        total_transformed = 0
        files_modified = 0
        root = Path(dirpath)

        # We need an AuditEngine just for the _iter_files helper
        from pyregex.application.services.audit.engine import AuditEngine

        audit = AuditEngine(registry=self.registry)

        files = [str(f) for f in audit._iter_files(root)]

        if max_workers and len(files) > 1:
            from concurrent.futures import ProcessPoolExecutor
            from pyregex.application.services.execution.worker import (
                unified_worker,
                WorkerResult,
            )

            reg_data = {"entities": self.registry.entities, "tags": self.registry.tags}
            params = {
                "pipeline": pipeline,
                "inplace": True if not output_dir else False,
            }

            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(unified_worker, "transform", f, params, reg_data)
                    for f in files
                ]
                for future in futures:
                    res: WorkerResult = future.result()
                    if res.success:
                        if res.items_count > 0:
                            total_transformed += res.items_count
                            files_modified += 1
                    else:
                        from pyregex.utils import ansi

                        print(
                            ansi.error(
                                f"Error transforming {res.filepath}: {res.error}"
                            )
                        )
            return total_transformed, files_modified

        # Sequential fallback
        for filepath in files:
            p = Path(filepath)
            out_p = Path(output_dir) / p.relative_to(root) if output_dir else None
            count = self.transform_file(p, destination=out_p, inplace=not out_p)
            if count > 0:
                total_transformed += count
                files_modified += 1
            if progress_callback:
                progress_callback()

        return total_transformed, files_modified

    def _transform_line(self, line: str) -> tuple[str, int]:
        """Applies all rules to a single line using interval-based non-overlapping replacement."""
        matches = []
        for name, pattern, action in self.compiled_rules:
            for match in pattern.finditer(line):
                matches.append(
                    (match.start(), match.end(), name, match.group(), action)
                )

        if not matches:
            return line, 0

        matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))

        filtered = []
        last_end = 0
        for m in matches:
            if m[0] >= last_end:
                filtered.append(m)
                last_end = m[1]

        from pyregex.application.services.mask.modes import MODES

        parts = []
        last_idx = 0
        count = 0
        for start, end, name, value, action in filtered:
            parts.append(line[last_idx:start])

            if action == "drop":
                return "", 1

            mode_func = MODES.get(action, MODES["redact"])
            parts.append(mode_func(value, self.mask_engine.salt, name))
            last_idx = end
            count += 1

        parts.append(line[last_idx:])
        return "".join(parts), count
