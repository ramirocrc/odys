import nox

PYTHON_VERSIONS = ["3.10", "3.11", "3.12", "3.13"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session: nox.Session) -> None:
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
