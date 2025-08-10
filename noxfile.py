"""Nox configuration for the optimes project.

This module defines the testing sessions and Python versions for the project.
"""

import nox

PYTHON_VERSIONS = ["3.9", "3.10", "3.11", "3.12", "3.13"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
    """Run the test suite with coverage reporting.

    Args:
        session: The nox session object.
    """
    session.install("uv")
    session.run("uv", "sync", "--active")
    session.run("python", "-c", "import sys; print(f'Running tests on Python {sys.version}')")
    session.run(
        "uv",
        "run",
        "python3",
        "-m",
        "pytest",
        "--doctest-modules",
        "tests",
        "--cov",
        "--cov-config=pyproject.toml",
        "--cov-report=xml",
    )
