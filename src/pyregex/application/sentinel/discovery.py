"""Sentinel Engine — Test Suite Discovery.

Recursively scans directories to locate and parse *.regex.yaml and *.regex.json
test suite files.
"""

from __future__ import annotations
from pathlib import Path
from typing import List

from pyregex.domain.sentinel.models import TestSuite
from pyregex.infrastructure.sentinel.parsers.yaml_parser import YamlSuiteParser


class TestDiscoverer:
    """Discovers and parses regex test suites inside directories."""

    def __init__(self):
        self.yaml_parser = YamlSuiteParser()

    def discover(self, path_str: str) -> List[TestSuite]:
        """Find and parse all test suites in the given path."""
        base_path = Path(path_str)
        if not base_path.exists():
            return []

        suites = []

        if base_path.is_file():
            if base_path.suffix in (".yaml", ".yml"):
                try:
                    suites.append(self.yaml_parser.parse(base_path))
                except Exception:
                    pass
            return suites

        # Directory scanning
        for file_path in base_path.rglob("*.regex.yaml"):
            try:
                suites.append(self.yaml_parser.parse(file_path))
            except Exception as e:
                # Log or handle parsing error here in a future update
                print(f"[Warn] Could not parse suite {file_path}: {e}")

        for file_path in base_path.rglob("*.regex.yml"):
            try:
                suites.append(self.yaml_parser.parse(file_path))
            except Exception as e:
                print(f"[Warn] Could not parse suite {file_path}: {e}")

        return suites
