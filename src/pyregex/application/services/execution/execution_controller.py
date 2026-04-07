from __future__ import annotations
from typing import TYPE_CHECKING, Any, List, Optional
from pyregex.application.services.execution.worker import unified_worker
from pyregex.infrastructure.execution.error_handling.execution_errors import (
    ExecutionError,
)

if TYPE_CHECKING:
    from pyregex.application.services.registry_controller import RegistryController


class ExecutionController:
    """Orchestrates pattern execution against targets."""

    def __init__(self, registry_system: RegistryController):
        self.registry_system = registry_system

    def execute(
        self,
        pattern: str,
        targets: List[str],
        args: Optional[Any] = None,
        callback: Optional[Any] = None,
    ) -> List[Any]:
        """Execute a pattern against multiple targets, optionally in parallel."""
        # Simplified for now to restore functionality
        results = []
        for target in targets:
            try:
                # Use the unified worker logic
                result = unified_worker(pattern, target, args)
                results.append(result)
                if callback:
                    callback(result)
            except Exception as e:
                raise ExecutionError(f"Error executing against {target}: {str(e)}")
        return results
