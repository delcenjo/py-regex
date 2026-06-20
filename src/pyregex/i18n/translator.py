"""Internationalization (i18n) system for PyRegex."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class Translator:
    """Handles localization of messages."""

    def __init__(self, language: str = "en"):
        self.language = language
        self.messages: dict[str, Any] = {}
        self._load_messages()

    def _load_messages(self) -> None:
        """Load messages from the locales directory."""
        # Now locales is packaged under src/pyregex/locales/ 
        current_dir = Path(__file__).parent
        locales_dir = current_dir.parent / "locales"

        # Fallback if not found
        if not locales_dir.exists():
            locales_dir = current_dir / "locales"

        lang_file = locales_dir / self.language / "messages.json"

        # Default to English if language file doesn't exist
        if not lang_file.exists():
            lang_file = locales_dir / "en" / "messages.json"

        if lang_file.exists():
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    self.messages = json.load(f)
            except (json.JSONDecodeError, OSError):
                self.messages = {}

    def t(self, key: str, fallback: Any = None, **kwargs: Any) -> Any:
        """Translate a key into the current language.

        Supports dot notation for nested keys (e.g., 'cli.errors.not_found').
        Supports keyword interpolation (e.g., 'Welcome, {name}').
        """
        keys = key.split(".")
        value = self.messages
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return fallback if fallback is not None else key

        if isinstance(value, str):
            try:
                return value.format(**kwargs)
            except (KeyError, ValueError):
                return value

        return value

    def has(self, key: str) -> bool:
        """Check if a translation key exists."""
        keys = key.split(".")
        value = self.messages
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return False
        return True


# Global translator instance (initialized in main)
_translator: Translator | None = None


def init_translator(language: str = "en") -> Translator:
    global _translator
    _translator = Translator(language)
    return _translator


def t(key: str, fallback: Any = None, **kwargs: Any) -> str:
    if _translator is None:
        return fallback if fallback is not None else key
    return _translator.t(key, fallback=fallback, **kwargs)


def has(key: str) -> bool:
    if _translator is None:
        return False
    return _translator.has(key)
