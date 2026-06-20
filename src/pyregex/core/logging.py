import logging
import sys

def setup_logger(name: str, level: str = "WARNING") -> logging.Logger:
    logger = logging.getLogger(f"pyregex.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%H:%M:%S"
        ))
        logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper(), logging.WARNING))
    return logger
