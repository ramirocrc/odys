"""Rich logging setup for development use."""

import logging

from rich.logging import RichHandler
from rich.traceback import install as install_rich_traceback


def setup_rich_logging() -> None:
    """Configure rich logging and tracebacks for development use."""
    logging.basicConfig(
        level="NOTSET",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    install_rich_traceback(width=200)
