"""Entry point for PyRegex CLI."""

from __future__ import annotations

import sys
def main() -> int:
    """Bootstrap the application and run the CLI."""
    try:
        from pyregex.core.logging import setup_logger

        from pyregex.infrastructure.config.loader import ConfigLoader
        from pyregex.infrastructure.persistence.config_repository import ConfigRepository

        log_level = "DEBUG" if "--debug" in sys.argv else "INFO" if "--verbose" in sys.argv else "WARNING"
        logger = setup_logger("main", level=log_level)
        logger.debug("Initializing PyRegex...")

        config_repo = ConfigRepository()
        loader = ConfigLoader(config_repo)
        config = loader.load_or_setup()

        # --- ALPHA-BYPASS: True Lightning Fast Startup ---
        # If we just want the assistant, don't even load the CLI registry/parser
        if len(sys.argv) > 1 and sys.argv[1] in ("assistant", "create", "asistente"):
            cmd = sys.argv[1]
            # Minimal init for the assistant
            from pyregex.container import AppContainer
            from pyregex.presentation.assistant.shell.repl import NebulaREPL
            
            container = AppContainer.create_default(config)
            repl = NebulaREPL(cli=None, config=config)
            
            # Inject container-level catalog into repl engine
            repl.engine.catalog_registry = container.catalog
            
            if cmd == "create":
                repl.run(initial_command="create")
            else:
                repl.run()
            return 0

        # 3. Create Container
        from pyregex.container import AppContainer
        from pyregex.i18n import translator as i18n
        from pyregex.presentation.cli.cli import PyRegexCLI

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
