# ABOUTME: Centralized logging configuration for WriteIt
# ABOUTME: Provides structured logging with configurable levels and file rotation

import logging
import logging.handlers
from pathlib import Path
from typing import Optional
import sys


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    enable_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> logging.Logger:
    """Setup centralized logging for WriteIt.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        enable_console: Whether to log to console
        max_bytes: Maximum bytes per log file before rotation
        backup_count: Number of backup log files to keep

    Returns:
        Configured logger instance
    """
    # Create main logger
    logger = logging.getLogger("writeit")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)  # Console shows INFO and above
        logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)  # File logs everything
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(f"writeit.{name}")


def configure_default_logging(workspace_path: Optional[Path] = None) -> logging.Logger:
    """Configure default logging for WriteIt application.

    Args:
        workspace_path: Optional workspace path for log file location

    Returns:
        Main logger instance
    """
    # Determine log file location
    log_file = None
    if workspace_path:
        log_file = workspace_path / "logs" / "writeit.log"

    # Setup logging with default configuration
    return setup_logging(log_level="INFO", log_file=log_file, enable_console=True)
