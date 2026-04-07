import signal
from pathlib import Path
from dataclasses import dataclass, field
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from pyregex.core.shared.exceptions import ExecutionTimeoutError


@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise ExecutionTimeoutError(f"Execution timed out after {seconds} seconds.")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


@dataclass
class WorkerResult:
    """Standard result from a parallel worker task."""

    filepath: str
    success: bool
    items_count: int = 0
    error: Optional[str] = None
    findings: List[Dict[str, Any]] = field(default_factory=list)


def unified_worker(
    task_type: str, filepath: str, params: Dict[str, Any], registry_data: Dict[str, Any]
) -> WorkerResult:
    """Unified entry point for all parallel workers (Audit, Mask, Transform).

    This function must be at the top level of a module to be picklable for
    multiprocessing. It reconstructs a local registry for each process.
    """
    from pyregex.application.services.registry import PatternRegistry

    try:
        # Reconstruct local registry for the process
        reg = PatternRegistry()
        reg.entities = registry_data.get("entities", {})
        reg.tags = registry_data.get("tags", {})

        path_obj = Path(filepath)
        if not path_obj.exists():
            return WorkerResult(
                filepath=filepath, success=False, error="File not found"
            )

        # Apply a hard timeout to prevent ReDoS
        timeout = params.get("timeout", 5)  # Default 5 seconds per file
        with time_limit(timeout):
            if task_type == "audit":
                from pyregex.application.services.audit.engine import AuditEngine

                engine = AuditEngine(registry=reg)
                compiled = engine._compile_patterns(
                    params["rules"], params.get("ignore_case", False)
                )
                findings = engine._scan_file(path_obj, compiled)
                if params.get("deep"):
                    findings = [f for f in findings if f.get("verified", True)]
                return WorkerResult(
                    filepath=filepath,
                    success=True,
                    items_count=len(findings),
                    findings=findings,
                )

            elif task_type == "mask":
                from pyregex.application.services.mask.engine import MaskEngine

                engine = MaskEngine(
                    mode=params["mode"], salt=params["salt"], registry=reg
                )
                count = engine.mask_file(
                    filepath,
                    params["rules"],
                    inplace=params["inplace"],
                    ignore_case=params.get("ignore_case", False),
                )
                return WorkerResult(filepath=filepath, success=True, items_count=count)

            elif task_type == "transform":
                from pyregex.application.services.transform_service import (
                    TransformEngine,
                )

                engine = TransformEngine(registry=reg)
                count = engine.transform_file(
                    path_obj, pipeline=params["pipeline"], inplace=params["inplace"]
                )
                return WorkerResult(filepath=filepath, success=True, items_count=count)

            elif task_type == "validate":
                from pyregex.application.services.validate.engine import ValidateEngine

                engine = ValidateEngine(registry=reg)
                res = engine.validate_regex(
                    params["type_name"],
                    filepath,
                    fail_fast=params.get("fail_fast", False),
                    column=params.get("column"),
                )
                return WorkerResult(
                    filepath=filepath,
                    success=True,
                    items_count=res.valid,
                    findings=[
                        {"line": e.line, "reason": e.reason, "value": e.value}
                        for e in res.errors
                    ],
                )

        return WorkerResult(
            filepath=filepath, success=False, error=f"Unknown task type: {task_type}"
        )
    except ExecutionTimeoutError as e:
        return WorkerResult(filepath=filepath, success=False, error=str(e))
    except Exception as e:
        return WorkerResult(filepath=filepath, success=False, error=str(e))
