"""
CogniFy Structured Logging
Loguru-based logging with consistent formatting
"""

import sys

from loguru import logger

from app.core.config import settings


def setup_logging(log_level: str | None = None) -> None:
    """Configure loguru for the application"""
    level = log_level or settings.LOG_LEVEL

    # Remove default handler
    logger.remove()

    # Add stderr handler with structured format
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        colorize=True,
    )


# Re-export logger for convenient import:
#   from app.core.logging import logger
__all__ = ["logger", "setup_logging"]
