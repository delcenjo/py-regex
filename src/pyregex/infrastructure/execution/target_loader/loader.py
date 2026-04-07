import os
from pathlib import Path
from typing import Generator, Tuple
from pyregex.infrastructure.execution.error_handling.execution_errors import (
    TargetNotFoundError,
    CorruptedFileError,
)


class BaseLoader:
    """Abstract base loader for streaming target execution."""

    def stream_chunks(self) -> Generator[Tuple[str, str, int], None, None]:
        """Yields (source_identifier, content_chunk, line_number)"""
        raise NotImplementedError


class StringLoader(BaseLoader):
    """Loads a direct inline string target."""

    def __init__(self, content: str):
        self.content = content

    def stream_chunks(self) -> Generator[Tuple[str, str, int], None, None]:
        yield ("<inline_string>", self.content, 1)


class FileLoader(BaseLoader):
    """Streams a file line-by-line to prevent massive OOM loops."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists() or not self.file_path.is_file():
            raise TargetNotFoundError(str(self.file_path))

    def stream_chunks(self) -> Generator[Tuple[str, str, int], None, None]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    # We yield line by line for huge logs, stripping the ending newline for cleaner matching
                    yield (str(self.file_path), line.rstrip("\n"), line_num)
        except UnicodeDecodeError:
            raise CorruptedFileError(
                str(self.file_path),
                "File violates UTF-8 string encoding limits. Binary file detected?",
            )
        except Exception as e:
            raise CorruptedFileError(str(self.file_path), str(e))


class DirectoryLoader(BaseLoader):
    """Recursively walks a directory, yielding streams from FileLoaders."""

    def __init__(self, dir_path: str, max_depth: int = -1):
        self.dir_path = Path(dir_path)
        if not self.dir_path.exists() or not self.dir_path.is_dir():
            raise TargetNotFoundError(str(self.dir_path))
        self.max_depth = max_depth

    def stream_chunks(self) -> Generator[Tuple[str, str, int], None, None]:
        for root, dirs, files in os.walk(self.dir_path):
            current_depth = root.replace(str(self.dir_path), "").count(os.sep)
            if self.max_depth > -1 and current_depth >= self.max_depth:
                # Don't recurse deeper if we hit max depth
                dirs[:] = []
                continue

            for file in files:
                file_path = os.path.join(root, file)
                loader = FileLoader(file_path)
                try:
                    for chunk in loader.stream_chunks():
                        yield chunk
                except CorruptedFileError:
                    # Skip binary or corrupted files in bulk directory scans
                    continue
