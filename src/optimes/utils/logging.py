import logging
from logging import Handler

from rich import traceback
from rich.logging import RichHandler


def get_handler() -> Handler:
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
