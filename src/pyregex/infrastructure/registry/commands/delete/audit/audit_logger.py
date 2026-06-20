from datetime import datetime
from pathlib import Path


class AuditLogger:
    """Logs enterprise-level deletion events."""

    def __init__(self, log_path: str = None):
        if not log_path:
            config_dir = Path.home() / ".pyregex"
            config_dir.mkdir(parents=True, exist_ok=True)
            log_path = config_dir / "registry_audit_log.txt"
        self.log_path = log_path

    def log_deletion(
        self, pattern_name: str, used_force: bool = False, is_soft: bool = True
    ):
        """Append-only logging."""
        timestamp = datetime.now().isoformat()
        mode = "FORCED" if used_force else "INTERACTIVE"
        action = "SOFT_DELETED" if is_soft else "HARD_DELETED"
        log_entry = f"[{timestamp}] [{mode}] {action}: {pattern_name}\n"

        with open(self.log_path, "a") as f:
            f.write(log_entry)
