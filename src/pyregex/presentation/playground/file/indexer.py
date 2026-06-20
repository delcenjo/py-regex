"""Playground File Mode — Line Offset Indexer.

Builds and caches a byte-offset index for instant random line access.
Memory-efficient: stores only int offsets, not line content.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class IndexInfo:
    """Metadata about a built index."""

    file_path: str
    file_size: int
    total_lines: int
    index_time_ms: float
    cache_hit: bool


class FileIndexer:
    """Builds and caches line-offset indexes for large files.

    The index maps each line number to its byte offset in the file,
    enabling O(1) random access to any line without scanning.

    For files scanned multiple times with different regex patterns,
    the index is built once and reused.

    Usage:
        indexer = FileIndexer()
        offsets = indexer.build("/var/log/syslog")
        # offsets[0] = byte offset of line 1
        # offsets[n] = byte offset of line n+1
    """

    # Directory for cached indexes
    _CACHE_DIR = Path.home() / ".pyregex" / "index_cache"

    def __init__(self, enable_cache: bool = True):
        self._enable_cache = enable_cache
        self._cache: dict[str, list[int]] = {}

    def build(self, file_path: str | Path) -> IndexInfo:
        """Build (or retrieve cached) line offset index.

        Returns IndexInfo with metadata about the indexing operation.
        The offsets are stored internally and can be retrieved via get_offsets().
        """
        path = Path(file_path).resolve()
        cache_key = self._cache_key(path)

        # Check memory cache first
        if cache_key in self._cache:
            return IndexInfo(
                file_path=str(path),
                file_size=path.stat().st_size,
                total_lines=len(self._cache[cache_key]),
                index_time_ms=0.0,
                cache_hit=True,
            )

        # Check disk cache
        if self._enable_cache:
            cached = self._load_disk_cache(path, cache_key)
            if cached is not None:
                self._cache[cache_key] = cached
                return IndexInfo(
                    file_path=str(path),
                    file_size=path.stat().st_size,
                    total_lines=len(cached),
                    index_time_ms=0.0,
                    cache_hit=True,
                )

        # Build fresh index
        t0 = time.perf_counter()
        offsets = self._scan_offsets(path)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        self._cache[cache_key] = offsets

        # Save to disk cache
        if self._enable_cache:
            self._save_disk_cache(path, cache_key, offsets)

        return IndexInfo(
            file_path=str(path),
            file_size=path.stat().st_size,
            total_lines=len(offsets),
            index_time_ms=elapsed_ms,
            cache_hit=False,
        )

    def get_offsets(self, file_path: str | Path) -> list[int]:
        """Get the cached offsets for a file. Build first if needed."""
        path = Path(file_path).resolve()
        key = self._cache_key(path)
        if key not in self._cache:
            self.build(path)
        return self._cache.get(key, [])

    def invalidate(self, file_path: str | Path) -> None:
        """Remove a file's index from all caches."""
        path = Path(file_path).resolve()
        key = self._cache_key(path)
        self._cache.pop(key, None)

        cache_file = self._CACHE_DIR / f"{key}.json"
        if cache_file.exists():
            cache_file.unlink()

    def clear_all(self) -> None:
        """Clear all cached indexes."""
        self._cache.clear()
        if self._CACHE_DIR.exists():
            for f in self._CACHE_DIR.glob("*.json"):
                f.unlink()

    # ── Internal ─────────────────────────────────────────────────

    def _scan_offsets(self, path: Path) -> list[int]:
        """Scan file and build byte offset list."""
        offsets = [0]
        with open(path, "rb") as f:
            while True:
                line = f.readline()
                if not line:
                    break
                offsets.append(offsets[-1] + len(line))

        # Remove trailing offset if it's past EOF
        file_size = path.stat().st_size
        if offsets and offsets[-1] >= file_size:
            offsets.pop()

        return offsets

    @staticmethod
    def _cache_key(path: Path) -> str:
        """Generate cache key from file path + size + mtime."""
        stat = path.stat()
        raw = f"{path}:{stat.st_size}:{stat.st_mtime_ns}"
        return hashlib.md5(raw.encode()).hexdigest()

    def _load_disk_cache(self, path: Path, key: str) -> Optional[list[int]]:
        """Load index from disk cache if valid."""
        cache_file = self._CACHE_DIR / f"{key}.json"
        if not cache_file.exists():
            return None

        try:
            data = json.loads(cache_file.read_text())
            # Validate against current file
            if data.get("size") == path.stat().st_size:
                return data["offsets"]
        except Exception:
            pass
        return None

    def _save_disk_cache(self, path: Path, key: str, offsets: list[int]) -> None:
        """Save index to disk cache."""
        try:
            self._CACHE_DIR.mkdir(parents=True, exist_ok=True)
            cache_file = self._CACHE_DIR / f"{key}.json"
            data = {
                "path": str(path),
                "size": path.stat().st_size,
                "lines": len(offsets),
                "offsets": offsets,
            }
            cache_file.write_text(json.dumps(data))
        except Exception:
            pass  # Non-critical failure
