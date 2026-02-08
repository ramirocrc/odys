"""Nox configuration for the odys project.

This module defines the testing sessions and Python versions for the project.
"""

import tomllib
from pathlib import Path

import nox

pyp = tomllib.loads(Path("pyproject.toml").read_text())

PYTHON_VERSIONS = [
    pv.rsplit(" ")[-1] for pv in pyp["project"]["classifiers"] if pv.startswith("Programming Language :: Python ::")
]


@nox.session(python=PYTHON_VERSIONS, venv_backend="uv")
@nox.parametrize("resolution", ["highest", "lowest-direct"])
def test_integration(session: nox.Session, resolution: str) -> None:
    """Run the test suite with coverage reporting.

    Args:
        session: The nox session object.
        resolution: Dependencies resolution strategy
    """
    session.run_always("uv", "pip", "install", ".", "--resolution", resolution, external=True)
    session.install("pytest", "pytest-xdist", "pytest-cov")
    session.run(
        "python",
        "-c",
        "import sys; print(f'Running tests on Python {sys.version}')",
    )
    session.run(
        "python",
        "-m",
        "pytest",
        "-n",
        "auto",
        "tests/integration",
    )
