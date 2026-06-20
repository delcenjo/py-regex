"""Sentinel Engine — YAML Parser for declarative Test Suites.

Loads *.regex.yaml files into TestSuite domain models.
"""

from __future__ import annotations
import yaml
from pathlib import Path

from pyregex.domain.sentinel.models import TestSuite, TestCase


class YamlSuiteParser:
    """Parses Sentinel Test Suites from YAML definition files."""

    def parse(self, filepath: str | Path) -> TestSuite:
        """Parse a YAML file and return a TestSuite object."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Test suite file not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in test suite {path}: {e}")

        if not isinstance(data, dict):
            raise ValueError(f"Test suite {path} must contain a top-level dictionary.")

        name = data.get("name", path.stem)
        pattern = data.get("pattern")
        if not pattern:
            raise ValueError(
                f"Test suite {path} is missing the required 'pattern' field."
            )

        description = data.get("description")
        tags = data.get("tags", [])

        # Fuzzer config
        fuzz_config = data.get("fuzz", {})
        fuzz_enabled = fuzz_config.get("enabled", False)
        fuzz_types = fuzz_config.get("types", [])
        fuzz_count = fuzz_config.get("count", 100)

        suite = TestSuite(
            name=name,
            pattern=pattern,
            description=description,
            tags=tags,
            fuzz_enabled=fuzz_enabled,
            fuzz_types=fuzz_types,
            fuzz_count=fuzz_count,
        )

        tests_data = data.get("tests", {})
        if not isinstance(tests_data, dict):
            tests_data = {}

        # Parse passes
        for item in tests_data.get("passes", []):
            if isinstance(item, str):
                suite.cases.append(TestCase(input_text=item, should_match=True))
            elif isinstance(item, dict) and "input" in item:
                suite.cases.append(
                    TestCase(
                        input_text=item["input"],
                        should_match=True,
                        expected_groups=item.get("groups"),
                    )
                )

        # Parse fails
        for item in tests_data.get("fails", []):
            if isinstance(item, str):
                suite.cases.append(TestCase(input_text=item, should_match=False))
            elif isinstance(item, dict) and "input" in item:
                suite.cases.append(
                    TestCase(input_text=item["input"], should_match=False)
                )

        return suite
