"""Configuration loading and first-run setup logic."""

from __future__ import annotations


from pyregex.infrastructure.config.models import AppConfig
from pyregex.infrastructure.persistence.config_repository import ConfigRepository
from pyregex.utils import ansi


class ConfigLoader:
    """Handles loading config and interactive setup."""

    def __init__(self, repo: ConfigRepository):
        self.repo = repo

    def load_or_setup(self) -> AppConfig:
        """Load config or run setup if it doesn't exist."""
        if not self.repo.exists():
            return self.run_interactive_setup()
        return self.repo.load()

    def run_interactive_setup(self) -> AppConfig:
        """Run interactive CLI setup for first-time users."""
        config = AppConfig()

        ansi.print_banner("PyRegex First-Time Setup")

        print("Welcome! Let's configure PyRegex.")

        lang = input("Select language [en/es] (default: en): ").strip().lower()
        if lang in ("en", "es"):
            config.language = lang

        region = (
            input("Enter your region [e.g. US, ES] (default: US): ").strip().upper()
        )
        if region:
            config.region = region

        theme = input("Select theme [dark/light] (default: dark): ").strip().lower()
        if theme in ("dark", "light"):
            config.theme = theme

        examples = (
            input("Show examples by default? [y/n] (default: y): ").strip().lower()
        )
        if examples:
            config.show_examples = examples in ("y", "yes", "s", "sí", "si")

        self.repo.save(config)

        print(
            ansi.success(
                f"\nSetup complete! Configuration saved to {self.repo.get_path()}"
            )
        )
        ansi.print_separator()

        return config
