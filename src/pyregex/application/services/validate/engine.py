import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any

from pyregex.infrastructure.registry import registry as global_registry
from pyregex.application.services.validate.regexes import (
    VALIDATORS,
    luhn_check,
    iban_check,
    nif_check,
)


@dataclass
class ValidationError:
    line: int
    column: int
    value: str
    reason: str


@dataclass
class ValidationResult:
    total: int = 0
    valid: int = 0
    errors: list = field(default_factory=list)
    source: str = ""
    type_name: str = ""

    @property
    def invalid(self) -> int:
        return self.total - self.valid

    @property
    def percentage(self) -> float:
        return (self.valid / self.total * 100) if self.total > 0 else 0.0


class ValidateEngine:
    """Core engine for validating data against regex patterns or JSON schemas."""

    def __init__(self, registry=None):
        self.registry = registry or global_registry

    def validate_regex(
        self,
        type_name: str,
        path: str,
        fail_fast: bool = False,
        column: Optional[int] = None,
        custom_regex: Optional[str] = None,
    ) -> ValidationResult:
        """Validates each line (or CSV column) of a file against a known regex type."""
        needs_luhn = False
        needs_iban = False
        needs_nif = False

        if custom_regex:
            pattern_str = custom_regex
        else:
            pattern_str = self.registry.get_pattern(type_name)

            # Fallback to hardcoded VALIDATORS for specific metadata like luhn_check
            if type_name in VALIDATORS:
                entry = VALIDATORS[type_name]
                if isinstance(entry, dict):
                    pattern_str = entry["pattern"]
                    needs_luhn = entry.get("luhn_check", False)
                    needs_iban = entry.get("iban_check", False)
                    needs_nif = entry.get("nif_check", False)
                elif not pattern_str:
                    if isinstance(entry, str):
                        pattern_str = entry

            if not pattern_str:
                available = ", ".join(self.registry.list_entities())
                raise ValueError(
                    f"Unknown type '{type_name}'. Available: {available} (or custom regex via --regex)"
                )

        regex = re.compile(pattern_str)
        result = ValidationResult(source=path, type_name=type_name)
        filepath = Path(path)

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                for line_num, raw_line in enumerate(f, 1):
                    line = raw_line.strip()
                    if not line:
                        continue

                    result.total += 1
                    value = line

                    # CSV column mode
                    if column is not None:
                        # Defensive hint for type checker
                        val_col = int(column)
                        parts = line.split(",")
                        if val_col < len(parts):
                            value = parts[val_col].strip().strip('"').strip("'")
                        else:
                            result.errors.append(
                                ValidationError(
                                    line=line_num,
                                    column=val_col + 1,
                                    value=line,
                                    reason=f"Column {val_col + 1} not found (only {len(parts)} columns)",
                                )
                            )
                            if fail_fast:
                                break
                            continue

                    if regex.match(value):
                        is_valid = True
                        if needs_luhn and not luhn_check(value):
                            is_valid = False
                            reason = "Regex OK but Luhn checksum failed"
                        elif needs_iban and not iban_check(value):
                            is_valid = False
                            reason = "Regex OK but IBAN checksum failed"
                        elif needs_nif and not nif_check(value):
                            is_valid = False
                            reason = "Regex OK but NIF/DNI checksum failed"

                        if not is_valid:
                            result.errors.append(
                                ValidationError(
                                    line=line_num, column=1, value=value, reason=reason
                                )
                            )
                            if fail_fast:
                                break
                        else:
                            result.valid += 1
                    else:
                        result.errors.append(
                            ValidationError(
                                line=line_num,
                                column=1,
                                value=value,
                                reason="Format invalid",
                            )
                        )
                        if fail_fast:
                            break

        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")

        return result

    def validate_directory(
        self,
        dirpath: str,
        type_name: str,
        exclude: Optional[list[str]] = None,
        fail_fast: bool = False,
        max_workers: Optional[int] = None,
        progress_callback: Optional[Any] = None,
    ) -> list[ValidationResult]:
        """Validates all files in a directory using parallel workers if specified."""
        results = []
        root = Path(dirpath)
        exclude = exclude or []

        if max_workers:
            from concurrent.futures import ProcessPoolExecutor
            from pyregex.application.services.execution.worker import (
                unified_worker,
                WorkerResult,
            )
            from pyregex.application.services.audit.engine import AuditEngine

            # Use AuditEngine's file iterator for consistency
            audit = AuditEngine(registry=self.registry)
            files = [
                str(f)
                for f in audit._iter_files(root)
                if not (exclude and any(re.search(ex, str(f)) for ex in exclude))
            ]

            reg_data = {"entities": self.registry.entities, "tags": self.registry.tags}
            params = {"type_name": type_name, "fail_fast": fail_fast}

            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(unified_worker, "validate", f, params, reg_data)
                    for f in files
                ]
                for future in futures:
                    res: WorkerResult = future.result()
                    # Convert WorkerResult back to a ValidationResult for consistency
                    v_res = ValidationResult(source=res.filepath, type_name=type_name)
                    v_res.valid = res.items_count
                    for f in res.findings:
                        v_res.errors.append(
                            ValidationError(
                                line=f["line"],
                                column=0,
                                value=f["value"],
                                reason=f["reason"],
                            )
                        )
                    results.append(v_res)
                    if progress_callback:
                        progress_callback()
            return results
        from pyregex.application.services.audit.engine import AuditEngine

        audit = AuditEngine(registry=self.registry)
        for filepath in audit._iter_files(root):
            if exclude and any(re.search(ex, str(filepath)) for ex in exclude):
                continue
            results.append(
                self.validate_regex(type_name, str(filepath), fail_fast=fail_fast)
            )
            if progress_callback:
                progress_callback()
        return results

    def validate_schema(self, schema_path: str, data_path: str) -> ValidationResult:
        """Validates JSON data against a JSON Schema file."""
        try:
            import jsonschema
        except ImportError:
            raise ImportError(
                "jsonschema is required for schema validation. Install with: pip install jsonschema"
            )

        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        result = ValidationResult(source=data_path, type_name="json_schema")

        # If data is a list, validate each item
        items = data if isinstance(data, list) else [data]
        result.total = len(items)

        for i, item in enumerate(items, 1):
            validator = jsonschema.Draft7Validator(schema.get("items", schema))
            errors = list(validator.iter_errors(item))
            if errors:
                for err in errors:
                    json_path = ".".join(str(p) for p in err.absolute_path) or "(root)"
                    result.errors.append(
                        ValidationError(
                            line=i,
                            column=0,
                            value=str(err.instance)[:50],
                            reason=f"{json_path}: {err.message}",
                        )
                    )
            else:
                result.valid += 1

        return result
