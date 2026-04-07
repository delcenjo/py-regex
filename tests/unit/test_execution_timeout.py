import pytest
from pyregex.application.services.execution.worker import unified_worker
from pyregex.core.shared.exceptions import ExecutionTimeoutError

def test_unified_worker_timeout(temp_dir):
    """Verify that an evil regex against a large string triggers a timeout."""
    # Create a test file with a long string designed to trigger ReDoS with the evil regex
    test_file = temp_dir / "evil.txt"
    test_file.write_text("a" * 80 + "!")

    # Mock registry so resolution finds our evil pattern
    registry_data = {
        "entities": {
            "EVIL_REGEX": "(a+)+$"
        },
        "tags": {}
    }

    params = {
        "rules": ["EVIL_REGEX"],  # Lookup by name
        "timeout": 1  # 1 second timeout
    }
    
    # We use 'audit' task type to invoke the scan
    result = unified_worker("audit", str(test_file), params, registry_data=registry_data)
    
    # The worker catches the ExecutionTimeoutError and returns it in the result.error
    assert result.success is False
    assert "Execution timed out" in str(result.error)
