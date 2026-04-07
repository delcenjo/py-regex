from __future__ import annotations
import sys
from abc import ABC, abstractmethod
from typing import Iterator


class InputReader(ABC):
    """Base class for all data input sources."""

    @abstractmethod
    def read_lines(self) -> Iterator[str]:
        pass


class StringReader(InputReader):
    """Reads from a static string."""

    def __init__(self, text: str):
        self.text = text

    def read_lines(self) -> Iterator[str]:
        yield from self.text.splitlines()


class FileReader(InputReader):
    """Reads from a file path with efficient chunking."""

    def __init__(self, path: str, chunk_size: int = 1024 * 1024):
        self.path = path
        self.chunk_size = chunk_size

    def read_lines(self) -> Iterator[str]:
        with open(self.path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                yield line.rstrip("\n")


class StreamReader(InputReader):
    """Reads from a stream (like sys.stdin) for real-time processing."""

    def __init__(self, stream=None):
        self.stream = stream or sys.stdin

    def read_lines(self) -> Iterator[str]:
        # Non-blocking or line-buffered read
        for line in self.stream:
            yield line.rstrip("\n")
