"""
Structured logging setup for TranslateGemma.
Usage:
    from logger import get_logger
    log = get_logger(__name__)
    log.info("Translation started", extra={"source": "en", "target": "zh"})
"""

import logging
import logging.handlers
import sys
from config import LOG_LEVEL, LOG_FORMAT, LOG_TO_FILE, LOG_FILE


def get_logger(name: str) -> logging.Logger:
    """Get or create a named logger with console + optional file output."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    formatter = logging.Formatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # File handler (rotating, 10 MB x 5 backups)
    if LOG_TO_FILE:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                str(LOG_FILE), maxBytes=10 * 1024 * 1024, backupCount=5,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError:
            logger.warning("Failed to create log file at %s", LOG_FILE)

    logger.propagate = False
    return logger
