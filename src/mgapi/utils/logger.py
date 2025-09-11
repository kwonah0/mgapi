"""Logging configuration for MGAPI."""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

from ..config import settings


def setup_logger(
    name: str = "mgapi",
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
) -> logging.Logger:
    """Set up a logger with Rich formatting.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    log_level = level or settings.get("log_level", "INFO")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    console_handler = RichHandler(
        console=Console(stderr=True),
        show_time=True,
        show_path=False,
        markup=True,
    )
    console_handler.setFormatter(
        logging.Formatter("%(message)s", datefmt="[%X]")
    )
    logger.addHandler(console_handler)
    
    if log_file or settings.get("log_file"):
        file_path = log_file or Path(settings.get("log_file"))
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(file_path)
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(file_handler)
    
    return logger


logger = setup_logger()