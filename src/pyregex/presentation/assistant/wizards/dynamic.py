"""Universal Nebula Wizard driven by catalog metadata.

This wizard eliminate the need for individual generated wizard classes
by rendering the Nebula UI directly from YAML metadata.
"""

from __future__ import annotations
from typing import Any, List, Dict

from pyregex.domain.catalog.registry import CatalogEntry
from pyregex.domain.builders.generic import GenericBuilder
from pyregex.presentation.assistant.wizards.base import BaseWizard
from pyregex.presentation.assistant.wizards.step import WizardStep, menu_step, text_step
from pyregex.i18n import translator as i18n
import importlib


class DynamicWizard(BaseWizard):
    """A generic wizard that renders UI from a CatalogEntry."""

    def __init__(self, entry: CatalogEntry, cli: Any = None):
        super().__init__(cli=cli)
        self.entry = entry
        
        # Configure metadata
        self.name = entry.name
        self.display_name = entry.wizard.get("display_name", entry.name.replace("_", " ").title())
        self.description = entry.description
        
        # 1. Hybrid Logic: Lazy load custom handler if specified
        self._handler = None
        if entry.logic_handler:
            self._handler = self._load_handler(entry.logic_handler)
            
        # 2. Internal builder to reuse logic (for 90% YAML cases)
        self._builder = GenericBuilder(entry)

    def _load_handler(self, handler_path: str) -> Any:
        """Lazy load a Python class from a string path (e.g. 'pyregex.handlers.sql.SQLHandler')."""
        try:
            module_path, class_name = handler_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            handler_class = getattr(module, class_name)
            # Instantiate with CLI for interaction
            return handler_class(cli=self.cli)
        except Exception:
            # Fallback to standard if handler fails
            return None

    def define_steps(self) -> list[WizardStep]:
        """Build steps from catalog entry, delegating to handler if complex."""
        # 10% Custom Logic: Let the handler define steps
        if self._handler is not None and hasattr(self._handler, "define_steps"):
            return self._handler.define_steps(self.entry)

        # 90% Standard Logic
        steps = []

        # 1. Subtype Selection (if catalog has subtypes)
        if self.entry.subtypes:
            choices = []
            for subtype_name, config in self.entry.subtypes.items():
                # Try to translate subtype display name
                display_name = config.get("display_name")
                if not display_name:
                    # Fallback to catalog name, then try i18n
                    catalog_key = f"catalog.{self.entry.name}.subtypes.{subtype_name}"
                    if i18n.has(catalog_key):
                        display_name = i18n.t(catalog_key)
                    else:
                        display_name = subtype_name.replace("_", " ").title()
                
                choices.append((subtype_name, display_name))

            title = i18n.t("assistant.wizards.select_variant")
            # If after translation it's still the key, use "Select Variant"
            if title == "assistant.wizards.select_variant":
                title = "Select Variant"

            # DEBUG
            # print(f"DEBUG: {self.entry.name} choices: {choices}")

            steps.append(
                menu_step("subtype", title, choices, default=self.entry.default_subtype)
            )
        
        # 2. Universal Config Schema (e.g., region, separators)
        if self.entry.config_schema:
            steps.extend(self._parse_config_schema(self.entry.config_schema))
            
        return steps

    def _parse_config_schema(self, schema: Dict[str, Any]) -> List[WizardStep]:
        steps = []
        for s_id, s in schema.items():
            s_type = s.get("type", "menu")
            s_title = s.get("title", s_id.replace("_", " ").title())
            
            if s_type == "menu":
                raw_choices = s.get("choices", [])
                choices = []
                for c in raw_choices:
                    if isinstance(c, (list, tuple)) and len(c) >= 2:
                        choices.append((str(c[0]), str(c[1])))
                    else:
                        choices.append((str(c), str(c).title()))
                steps.append(menu_step(s_id, s_title, choices, default=s.get("default")))
            elif s_type == "text":
                steps.append(text_step(s_id, s_title, prompt=s.get("prompt", "> "), default=s.get("default")))
        return steps

    def _parse_manual_steps(self, steps_cfg: List[Dict[str, Any]]) -> List[WizardStep]:
        steps = []
        for s in steps_cfg:
            s_type = s.get("type", "menu")
            s_id = s.get("id", "step")
            s_title = s.get("title", s_id.title())
            
            if s_type == "menu":
                # Handle choices format: [[key, label], ...] or [key, ...]
                raw_choices = s.get("choices", [])
                choices = []
                for c in raw_choices:
                    if isinstance(c, (list, tuple)) and len(c) >= 2:
                        choices.append((str(c[0]), str(c[1])))
                    else:
                        choices.append((str(c), str(c).title()))
                steps.append(menu_step(s_id, s_title, choices))
            elif s_type == "text":
                steps.append(text_step(s_id, s_title, prompt=s.get("prompt", "> ")))
                
        return steps

    def build_pattern(self, answers: dict[str, Any]) -> str:
        """Build the pattern, delegating to handler if complex."""
        if self._handler is not None and hasattr(self._handler, "build_pattern"):
            return self._handler.build_pattern(answers, self.entry)

        self._builder.config.update(answers)
        return self._builder.build_pattern()

    def get_examples(self, answers: dict[str, Any], pattern: str) -> List[str]:
        """Get examples, delegating to handler if complex."""
        if self._handler is not None and hasattr(self._handler, "get_examples"):
            return self._handler.get_examples(answers, pattern, self.entry)

        self._builder.config.update(answers)
        return self._builder.get_examples()

    def get_non_examples(self, answers: dict[str, Any], pattern: str) -> List[str]:
        """Get non-examples, delegating to handler if complex."""
        if self._handler is not None and hasattr(self._handler, "get_non_examples"):
            return self._handler.get_non_examples(answers, pattern, self.entry)

        self._builder.config.update(answers)
        return self._builder.get_non_examples()
