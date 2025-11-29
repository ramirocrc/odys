"""Nox configuration for the optimes project.

This module defines the testing sessions and Python versions for the project.
"""

import nox

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13", "3.14"]


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("resolution", ["highest", "lowest-direct"])
def test_integration(session: nox.Session, resolution: str) -> None:
    """Run the test suite with coverage reporting.

    Args:
        session: The nox session object.
        resolution: Dependencies resolution strategy
    """
    session.install("uv")
    session.run("uv", "pip", "install", "-e", ".", "--resolution", resolution)
    session.run(
        "python",
        "-c",
        "import sys; print(f'Running tests on Python {sys.version}')",
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
