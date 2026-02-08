"""Logging utilities for the odys project.

This module provides logging utilities including rich formatting
and traceback handling for better debugging experience.
"""

import logging
from logging import Handler

from rich import traceback
from rich.logging import RichHandler


def get_handler() -> Handler:
    """Get a rich logging handler with traceback formatting.

    Returns:
        A configured RichHandler instance with traceback formatting.
    """
    rich_handler = RichHandler(rich_tracebacks=True, tracebacks_show_locals=False)
    traceback.install(width=200)
    return rich_handler


handler = get_handler()


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger
