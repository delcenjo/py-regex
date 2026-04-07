"""Entry point for PyRegex CLI."""

from __future__ import annotations

import sys
from pathlib import Path
from pyregex.presentation.cli.cli import PyRegexCLI
from pyregex.infrastructure.config.loader import ConfigLoader
from pyregex.infrastructure.persistence.config_repository import ConfigRepository
from pyregex.container import AppContainer
from pyregex.i18n import translator as i18n


def main() -> int:
    """Bootstrap the application and run the CLI."""
    try:
        import os
        from pyregex.core.logging import setup_logger

        log_level = "DEBUG" if "--debug" in sys.argv else "INFO" if "--verbose" in sys.argv else "WARNING"
        logger = setup_logger("main", level=log_level)
        logger.debug("Initializing PyRegex...")

        config_repo = ConfigRepository()

        # 2. Load or run setup
        loader = ConfigLoader(config_repo)
        config = loader.load_or_setup()

        # 3. Create Container
        container = AppContainer.create_default(config)

        # 4. Initialize i18n
        i18n.init_translator(config.language)

        # 5. Run CLI
        cli = PyRegexCLI(container)
        return cli.run()

    except KeyboardInterrupt:
        print("\nAborted.")
        return 1
    except Exception as e:
        if 'logger' in locals():
            logger.fatal("Fatal error: %s", e, exc_info=True)
        else:
            print(f"\nFatal error: {e}")
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
