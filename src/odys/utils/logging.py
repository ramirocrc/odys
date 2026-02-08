"""Logging utilities for the odys project."""

import logging

from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)


def setup_rich_logging() -> None:
    """Configure rich logging and tracebacks for development use."""
    logging.basicConfig(
        level="NOTSET",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    install_rich_traceback(width=200)
