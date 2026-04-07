#!/usr/bin/env python3
"""Catalog-Driven Builder & Wizard Generator.

Reads YAML catalog files and generates validated Python builder + wizard files.

Usage:
    python scripts/generate_builders.py                    # Generate all
    python scripts/generate_builders.py --category personal  # Generate one category
    python scripts/generate_builders.py --validate-only      # Validate without writing
    python scripts/generate_builders.py --stats              # Show generation stats
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import textwrap
from pathlib import Path
from typing import Any

import yaml

# ── Paths ────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CATALOG_DIR = PROJECT_ROOT / "catalog"
BUILDERS_DIR = PROJECT_ROOT / "src" / "pyregex" / "domain" / "builders"
WIZARDS_DIR = PROJECT_ROOT / "src" / "pyregex" / "presentation" / "assistant" / "modules"


# ── Templates ────────────────────────────────────────────────────────

BUILDER_TEMPLATE = '''\
r"""{description}

Auto-generated builder. Do not edit manually.
Edit the YAML catalog entry instead and re-run generate_builders.py.
"""

from __future__ import annotations

import re
from typing import Any, Pattern

from pyregex.domain.builders.base import RegexBuilder, BuilderMetadata, register_builder


@register_builder("{register_name}")
class {class_name}(RegexBuilder):
    r"""{description}

    Subtypes:
{subtypes_doc}
    """

    def __init__(self, subtype: str = "{default_subtype}"):
        self.subtype = subtype.lower()

    @property
    def metadata(self) -> BuilderMetadata:
        return BuilderMetadata(
            name="{register_name}",
            category="{category}",
            description="{description}",
            examples={examples},
            non_examples={non_examples},
        )

    def default_config(self) -> dict[str, Any]:
        return {{"subtype": "{default_subtype}"}}

    def build(self, config: dict[str, Any] | None = None) -> Pattern[str]:
        cfg = self.default_config()
        if config:
            cfg.update(config)
        self.subtype = str(cfg.get("subtype", "{default_subtype}")).lower()
        return re.compile(self.build_pattern())

    def build_pattern(self) -> str:
{build_pattern_body}
        # Default
        return {default_pattern}
'''

WIZARD_TEMPLATE = '''\
r"""{description}

Auto-generated wizard. Do not edit manually.
Edit the YAML catalog entry instead and re-run generate_builders.py.
"""

from __future__ import annotations
from typing import Any

from pyregex.presentation.assistant.wizards.base import BaseWizard
from pyregex.presentation.assistant.wizards.step import menu_step, text_step, WizardStep
from pyregex.domain.builders.{category}.{builder_module} import {builder_class}


class {wizard_class}(BaseWizard):
    name = "{wizard_name}"
    display_name = "{display_name}"
    description = "{description}"
    tags = {tags}

    def define_steps(self) -> list[WizardStep]:
        return [
{wizard_steps}
        ]

    def build_pattern(self, answers: dict[str, Any]) -> str:
        subtype = answers.get("subtype", "{default_subtype}")
        builder = {builder_class}(subtype=subtype)
        return builder.build_pattern()

    def get_examples(self, answers: dict, pattern: str) -> list[str]:
        builder = {builder_class}(subtype=answers.get("subtype", "{default_subtype}"))
        return builder.metadata.examples

    def get_non_examples(self, answers: dict, pattern: str) -> list[str]:
        builder = {builder_class}(subtype=answers.get("subtype", "{default_subtype}"))
        return builder.metadata.non_examples
'''


# ── Generator Core ───────────────────────────────────────────────────

def to_python_literal(s: str) -> str:
    """Returns a valid Python raw string literal for the given string."""
    if not s:
        return 'r""'
    # Try single quotes raw
    if "'" not in s and not s.endswith("\\"):
        return f"r'{s}'"
    # Try double quotes raw
    if '"' not in s and not s.endswith("\\"):
        return f'r"{s}"'
    # Try triple single quotes
    if "'''" not in s and not s.endswith("'"):
        return f"r'''{s}'''"
    # Try triple double quotes
    if '"""' not in s and not s.endswith('"'):
        return f'r"""{s}"""'
    # Fallback to repr (standard escaped string)
    return repr(s)


class CatalogGenerator:
    """Reads YAML catalogs and generates builder + wizard Python files."""

    def __init__(self, validate_only: bool = False, verbose: bool = True):
        self.validate_only = validate_only
        self.verbose = verbose
        self.stats = {
            "total_entries": 0,
            "builders_generated": 0,
            "wizards_generated": 0,
            "validation_passed": 0,
            "validation_failed": 0,
            "errors": [],
        }

    def run(self, category: str | None = None) -> dict:
        """Run the generator for all or a specific category."""
        if category:
            catalog_dirs = [CATALOG_DIR / category]
        else:
            catalog_dirs = sorted(CATALOG_DIR.iterdir())

        for cat_dir in catalog_dirs:
            if not cat_dir.is_dir():
                continue
            for yaml_file in sorted(cat_dir.glob("*.yaml")):
                self._process_catalog_file(yaml_file, cat_dir.name)

        return self.stats

    def _process_catalog_file(self, yaml_path: Path, category: str):
        """Process a single YAML catalog file."""
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                catalog = yaml.safe_load(f)
        except Exception as e:
            self.stats["errors"].append(f"Failed to parse {yaml_path}: {e}")
            return

        if not catalog or "entries" not in catalog:
            return

        for entry in catalog["entries"]:
            self.stats["total_entries"] += 1
            try:
                self._process_entry(entry, category)
            except Exception as e:
                self.stats["errors"].append(
                    f"Failed to process '{entry.get('name', '?')}': {e}"
                )

    def _process_entry(self, entry: dict, category: str):
        """Process a single catalog entry → generate builder + wizard."""
        name = entry["name"]
        class_name = entry["class_name"]
        description = entry.get("description", f"Regex builder for {name}")
        subtypes = entry.get("subtypes", {})

        if not subtypes:
            self.stats["errors"].append(f"'{name}' has no subtypes")
            return

        # ── Validate all patterns ──
        all_examples = []
        all_non_examples = []
        for st_name, st_data in subtypes.items():
            pattern = st_data.get("pattern", "")
            examples = st_data.get("examples", [])
            non_examples = st_data.get("non_examples", [])
            all_examples.extend(examples)
            all_non_examples.extend(non_examples)

            # Validate pattern compiles
            try:
                compiled = re.compile(pattern)
            except re.error as e:
                self.stats["validation_failed"] += 1
                self.stats["errors"].append(
                    f"'{name}.{st_name}': pattern doesn't compile: {e}"
                )
                return

            # Validate examples match
            for ex in examples:
                if not compiled.search(ex):
                    self.stats["validation_failed"] += 1
                    self.stats["errors"].append(
                        f"'{name}.{st_name}': example '{ex}' doesn't match pattern"
                    )
                    return

            # Validate non_examples don't match (fullmatch)
            for nex in non_examples:
                if compiled.fullmatch(nex):
                    self.stats["validation_failed"] += 1
                    self.stats["errors"].append(
                        f"'{name}.{st_name}': non_example '{nex}' incorrectly matches"
                    )
                    return

        self.stats["validation_passed"] += 1

        if self.validate_only:
            if self.verbose:
                print(f"  ✅ {name} ({len(subtypes)} subtypes)")
            return

        # ── Generate builder ──
        default_subtype = list(subtypes.keys())[0]

        # Build the if/elif chain for build_pattern
        pattern_lines = []
        for i, (st_name, st_data) in enumerate(subtypes.items()):
            p = st_data["pattern"]
            pattern_literal = to_python_literal(p)
            if i == 0:
                pattern_lines.append(
                    f'        if self.subtype == "{st_name}":\n'
                    f'            return {pattern_literal}'
                )
            else:
                pattern_lines.append(
                    f'        elif self.subtype == "{st_name}":\n'
                    f'            return {pattern_literal}'
                )

        # Subtypes docstring
        subtypes_doc = "\n".join(
            f"        - {st_name}: {st_data.get('pattern', '')[:60]}..."
            for st_name, st_data in subtypes.items()
        )

        builder_code = BUILDER_TEMPLATE.format(
            description=description,
            register_name=name,
            class_name=class_name,
            category=category,
            default_subtype=default_subtype,
            examples=repr(all_examples[:8]),
            non_examples=repr(all_non_examples[:8]),
            subtypes_doc=subtypes_doc,
            build_pattern_body="\n".join(pattern_lines),
            default_pattern=to_python_literal(subtypes[default_subtype]["pattern"]),
        )

        # Write builder file
        builder_module = f"{name}_builder"
        builder_dir = BUILDERS_DIR / category
        builder_dir.mkdir(parents=True, exist_ok=True)
        builder_path = builder_dir / f"{builder_module}.py"
        builder_path.write_text(builder_code, encoding="utf-8")
        self.stats["builders_generated"] += 1

        if self.verbose:
            print(f"  📦 {builder_path.relative_to(PROJECT_ROOT)}")

        # ── Generate wizard ──
        wizard_config = entry.get("wizard", {})
        if not wizard_config:
            return

        display_name = wizard_config.get("display_name", name.replace("_", " ").title())
        wizard_desc = wizard_config.get("description", description)
        tags = wizard_config.get("tags", [name, category])
        steps = wizard_config.get("steps", [])

        # Generate wizard step code
        wizard_step_lines = []
        for step in steps:
            step_type = step.get("type", "menu")
            key = step.get("key", "subtype")
            label = step.get("label", "Opción")

            if step_type == "menu":
                options = step.get("options", [])
                opts_str = ",\n".join(
                    f'                    ("{opt[0]}", "{opt[1]}")'
                    for opt in options
                )
                wizard_step_lines.append(
                    f'            menu_step(\n'
                    f'                "{key}",\n'
                    f'                "{label}",\n'
                    f'                [\n{opts_str},\n'
                    f'                ],\n'
                    f'            ),'
                )
            elif step_type == "text":
                wizard_step_lines.append(
                    f'            text_step(\n'
                    f'                "{key}",\n'
                    f'                "{label}",\n'
                    f'            ),'
                )

        # If no steps defined but subtypes exist, auto-generate a menu step
        if not wizard_step_lines and subtypes:
            opts_str = ",\n".join(
                f'                    ("{st_name}", "{st_name.replace("_", " ").title()}")'
                for st_name in subtypes.keys()
            )
            wizard_step_lines = [
                f'            menu_step(\n'
                f'                "subtype",\n'
                f'                "Tipo",\n'
                f'                [\n{opts_str},\n'
                f'                ],\n'
                f'            ),'
            ]

        wizard_class = class_name.replace("RegexBuilder", "Wizard")
        wizard_name = f"{name}_wizard"

        wizard_code = WIZARD_TEMPLATE.format(
            description=wizard_desc,
            category=category,
            builder_module=builder_module,
            builder_class=class_name,
            wizard_class=wizard_class,
            wizard_name=wizard_name,
            display_name=display_name,
            tags=repr(tags),
            wizard_steps="\n".join(wizard_step_lines),
            default_subtype=default_subtype,
        )

        # Write wizard file
        wizard_dir = WIZARDS_DIR / category
        wizard_dir.mkdir(parents=True, exist_ok=True)
        # Ensure __init__.py exists
        init_file = wizard_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f"# Nebula — {category.title()} Module Package\n")
        
        wizard_path = wizard_dir / f"{wizard_name}.py"
        wizard_path.write_text(wizard_code, encoding="utf-8")
        self.stats["wizards_generated"] += 1

        if self.verbose:
            print(f"  🧙 {wizard_path.relative_to(PROJECT_ROOT)}")


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate builders & wizards from YAML catalogs"
    )
    parser.add_argument(
        "--category", "-c",
        help="Generate only a specific category",
    )
    parser.add_argument(
        "--validate-only", "-v",
        action="store_true",
        help="Validate catalog without generating files",
    )
    parser.add_argument(
        "--stats", "-s",
        action="store_true",
        help="Show generation statistics",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress per-file output",
    )
    args = parser.parse_args()

    print(f"\n{'━' * 60}")
    print("  🏭 PyRegex Builder Generator")
    print(f"{'━' * 60}\n")

    generator = CatalogGenerator(
        validate_only=args.validate_only,
        verbose=not args.quiet,
    )

    stats = generator.run(category=args.category)

    # Print summary
    print(f"\n{'─' * 60}")
    print(f"  📊 Results:")
    print(f"     Catalog entries: {stats['total_entries']}")
    print(f"     Validation: {stats['validation_passed']} ✅ / {stats['validation_failed']} ❌")
    if not args.validate_only:
        print(f"     Builders generated: {stats['builders_generated']}")
        print(f"     Wizards generated: {stats['wizards_generated']}")

    if stats["errors"]:
        print(f"\n  ⚠️  Errors ({len(stats['errors'])}):")
        for err in stats["errors"][:20]:
            print(f"     • {err}")

    print(f"{'─' * 60}\n")

    return 0 if not stats["errors"] else 1


if __name__ == "__main__":
    sys.exit(main())
