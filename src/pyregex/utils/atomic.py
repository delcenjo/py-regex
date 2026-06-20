import os
import tempfile
from pathlib import Path


def atomic_write(path: Path, content: str, encoding: str = "utf-8") -> None:
    """
    Writes content to a file atomically.
    1. Writes to a temporary file in the same directory.
    2. Syncs to disk.
    3. Atomically replaces the target file.
    """
    path = Path(path)
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)

    # Use a temporary file in the same directory as the target (required for atomic rename)
    fd, temp_path = tempfile.mkstemp(dir=parent, prefix=f"{path.name}.tmp-", text=True)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, path)
    except Exception:
        # Cleanup temp file on failure
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
