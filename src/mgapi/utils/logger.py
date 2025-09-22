"""Logging configuration for MGAPI."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from ..config import settings


def setup_logger(level: Optional[str] = None, log_file: Optional[Path] = None) -> None:
    """Configure loguru logger.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging
    """
    # Remove default handler
    logger.remove()

    log_level = level or settings.get("log_level", "INFO")

    # Add console handler with minimal format
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level=log_level.upper(),
        colorize=True
    )

    # Add file handler if specified
    if log_file or settings.get("log_file"):
        file_path = log_file or Path(settings.get("log_file"))
        file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            file_path,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            level=log_level.upper(),
            rotation="10 MB",
            retention="7 days"
        )


# Initialize logger on import
setup_logger()