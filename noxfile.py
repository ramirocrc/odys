"""Nox configuration for the optimes project.

This module defines the testing sessions and Python versions for the project.
"""

import nox

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]


@nox.session(python=PYTHON_VERSIONS)
def test_integration_highest(session: nox.Session) -> None:
    """Run the test suite with coverage reporting.

    Args:
        session: The nox session object.
    """
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".", "--resolution", "highest")
    session.run(
        "python",
        "-c",
        "import sys; print(f'Running tests on Python {sys.version} (highest resolution)')",
    )
    session.run(
        "uv",
        "run",
        "python",
        "-m",
        "pytest",
        "-n",
        "auto",
        "tests/integration",
    )


@nox.session(python=PYTHON_VERSIONS)
def test_integration_lowest(session: nox.Session) -> None:
    """Run the test suite with coverage reporting.

    Args:
        session: The nox session object.
    """
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".", "--resolution", "lowest-direct")
    session.run(
        "python",
        "-c",
        "import sys; print(f'Running tests on Python {sys.version} (highest resolution)')",
    )
    session.run(
        "uv",
        "run",
        "python",
        "-m",
        "pytest",
        "-n",
        "auto",
        "tests/integration",
    )
