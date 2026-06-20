"""Playground — File Mode Engine.

Professional file-based regex matching with streaming processing,
live highlighting, and structured export.
"""

from pyregex.presentation.playground.file.reader import FileReader
from pyregex.presentation.playground.file.scanner import FileScanner, ScanMatch
from pyregex.presentation.playground.file.indexer import FileIndexer
from pyregex.presentation.playground.file.exporter import FileExporter

__all__ = ["FileReader", "FileScanner", "ScanMatch", "FileIndexer", "FileExporter"]
