"""Playground File Mode — Lazy File Reader.

Uses mmap for zero-copy reading of large files (up to multi-GB).
Provides line iteration, random access by line number, and encoding detection.
"""

from __future__ import annotations

import mmap
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional


@dataclass(frozen=True)
class FileInfo:
    """Metadata about the opened file."""

    path: str
    size_bytes: int
    encoding: str
    total_lines: int
    is_binary: bool


class FileReader:
    """Memory-mapped lazy file reader for large files.

    Supports:
    - Files from bytes to multi-GB via mmap
    - Line-by-line iteration without loading full file
    - Random access by line number via offset index
    - Encoding detection with fallback
    - Context-aware line retrieval (surrounding lines)

    Usage:
        reader = FileReader("/var/log/syslog")
        info = reader.open()
        for line_no, line in reader.iter_lines():
            print(f"{line_no}: {line}")
        reader.close()
    """

    _DETECT_CHUNK = 8192
    _MMAP_THRESHOLD = 10 * 1024 * 1024  # 10MB
    # Store one byte offset every N lines to bound index RAM usage.
    _SPARSE_STEP = 10000

    def __init__(self, file_path: str | Path):
        self._path = Path(file_path).resolve()
        self._fd: Optional[int] = None
        self._mm: Optional[mmap.mmap] = None
        self._data: Optional[bytes] = None  # for small files
        self._size: int = 0
        self._encoding: str = "utf-8"
        self._is_open: bool = False
        
        self._sparse_index: list[int] = [0]
        self._known_lines: int = 1
        self._index_complete = threading.Event()
        self._indexer_thread: Optional[threading.Thread] = None

    @property
    def path(self) -> str:
        return str(self._path)

    @property
    def filename(self) -> str:
        return self._path.name

    @property
    def size_bytes(self) -> int:
        return self._size

    @property
    def total_lines(self) -> int:
        return self._known_lines

    @property
    def is_index_complete(self) -> bool:
        return self._index_complete.is_set()

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def is_open(self) -> bool:
        return self._is_open

    def open(self) -> FileInfo:
        """Open the file and build line index.

        Returns FileInfo with metadata.
        Raises FileNotFoundError, PermissionError, or ValueError for binary files.
        """
        if not self._path.exists():
            raise FileNotFoundError(f"File not found: {self._path}")
        if not self._path.is_file():
            raise ValueError(f"Not a file: {self._path}")

        self._size = self._path.stat().st_size
        if self._size == 0:
            self._line_offsets = []
            self._is_open = True
            return FileInfo(
                path=str(self._path),
                size_bytes=0,
                encoding=self._encoding,
                total_lines=0,
                is_binary=False,
            )

        self._encoding = self._detect_encoding()
        is_binary = self._check_binary()
        if is_binary:
            raise ValueError(
                f"Binary file detected: {self._path.name} "
                "(playground only supports text files)"
            )

        if self._size <= self._MMAP_THRESHOLD:
            self._data = self._path.read_bytes()
        else:
            self._fd = os.open(str(self._path), os.O_RDONLY)
            self._mm = mmap.mmap(self._fd, 0, access=mmap.ACCESS_READ)

        self._index_complete.clear()
        self._sparse_index = [0]
        self._known_lines = 1
        self._is_open = True
        self._indexer_thread = threading.Thread(target=self._build_sparse_index_bg, daemon=True)
        self._indexer_thread.start()

        return FileInfo(
            path=str(self._path),
            size_bytes=self._size,
            encoding=self._encoding,
            total_lines=0,  # Dynamically updated
            is_binary=False,
        )

    def close(self) -> None:
        """Release all resources."""
        self._is_open = False
        if self._indexer_thread:
            self._indexer_thread.join(timeout=0.1)
            
        if self._mm is not None:
            self._mm.close()
            self._mm = None
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        self._data = None
        self._sparse_index = [0]
        self._known_lines = 0

    def __enter__(self) -> FileReader:
        self.open()
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def get_line(self, line_no: int) -> str:
        """Get a single line by 1-based line number."""
        for _, text in self.iter_lines(line_no, line_no):
            return text
        return ""

    def get_lines(self, start_line: int, end_line: int) -> list[tuple[int, str]]:
        """Get a range of lines (1-based, inclusive)."""
        if not self._is_open or start_line < 1:
            return []
        return list(self.iter_lines(start_line, end_line))

    def get_context(
        self, line_no: int, before: int = 2, after: int = 2
    ) -> list[tuple[int, str, bool]]:
        """Get a line with surrounding context."""
        start = max(1, line_no - before)
        end = line_no + after
        return [
            (n, text, n == line_no) 
            for n, text in self.iter_lines(start, end)
        ]

    def iter_lines(
        self, start_line: int = 1, end_line: Optional[int] = None
    ) -> Iterator[tuple[int, str]]:
        """Iterate lines lazily finding offsets via sparse index seeking."""
        if not self._is_open or start_line < 1:
            return

        data = self._data if self._data is not None else self._mm
        if data is None:
            return

        chunk_idx = (start_line - 1) // self._SPARSE_STEP
        if chunk_idx >= len(self._sparse_index):
            chunk_idx = len(self._sparse_index) - 1
            
        pos = self._sparse_index[chunk_idx]
        current_line = chunk_idx * self._SPARSE_STEP + 1
        
        while current_line < start_line and pos < self._size:
            nl = data.find(b"\n", pos)
            if nl == -1:
                return # EOF reached before start_line
            pos = nl + 1
            current_line += 1
            
        while pos < self._size and self._is_open:
            if end_line is not None and current_line > end_line:
                break
                
            nl = data.find(b"\n", pos)
            if nl == -1:
                raw = self._read_bytes(pos, self._size)
                yield current_line, raw.decode(self._encoding, errors="replace").rstrip("\n").rstrip("\r")
                break
                
            raw = self._read_bytes(pos, nl)
            yield current_line, raw.decode(self._encoding, errors="replace").rstrip("\r")
            
            pos = nl + 1
            current_line += 1

    def _read_bytes(self, start: int, end: int) -> bytes:
        """Read a byte range from the backing store."""
        if self._data is not None:
            return self._data[start:end]
        if self._mm is not None:
            return self._mm[start:end]
        return b""

    def _build_sparse_index_bg(self) -> None:
        """Background thread: build sparse line-offset index."""
        data = self._data if self._data is not None else self._mm
        if data is None:
            self._index_complete.set()
            return

        pos = 0
        line_count = 0
        size = self._size
        step = self._SPARSE_STEP
        
        while pos < size and self._is_open:
            nl = data.find(b"\n", pos)
            if nl == -1:
                break
                
            line_count += 1
            pos = nl + 1
            
            if line_count % step == 0:
                self._sparse_index.append(pos)
                
            self._known_lines = line_count + 1
            
        if pos < size:
            self._known_lines += 1
            
        self._index_complete.set()

    def _detect_encoding(self) -> str:
        """Simple encoding detection with fallback chain."""
        chunk = b""
        try:
            with open(self._path, "rb") as f:
                chunk = f.read(self._DETECT_CHUNK)
        except Exception:
            return "utf-8"

        if chunk.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig"
        if chunk.startswith(b"\xff\xfe"):
            return "utf-16-le"
        if chunk.startswith(b"\xfe\xff"):
            return "utf-16-be"

        try:
            chunk.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            pass

        # latin-1 always succeeds; treat as last resort
        return "latin-1"

    def _check_binary(self) -> bool:
        """Check if file appears to be binary."""
        try:
            with open(self._path, "rb") as f:
                chunk = f.read(self._DETECT_CHUNK)
        except Exception:
            return False

        if b"\x00" in chunk:
            return True

        non_text = sum(1 for b in chunk if b < 8 or (14 <= b < 32 and b != 27))
        return non_text / max(len(chunk), 1) > 0.10

    def __repr__(self) -> str:
        state = "open" if self._is_open else "closed"
        return (
            f"FileReader({self._path.name!r}, "
            f"{self._format_size(self._size)}, "
            f"{len(getattr(self, '_line_offsets', ()) or ())} lines, {state})"
        )

    @staticmethod
    def _format_size(size: int) -> str:
        for unit in ("B", "KB", "MB", "GB", "TB"):
            if size < 1024:
                return f"{size:.1f}{unit}" if unit != "B" else f"{size}{unit}"
            size /= 1024  # type: ignore
        return f"{size:.1f}PB"
