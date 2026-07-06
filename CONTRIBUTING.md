# Contributing to Odys

Thanks for your interest in contributing to Odys! Whether you're fixing a bug, adding a feature, or improving docs — your help is welcome.

## Code of Conduct

This project follows the MIT License spirit: be respectful, constructive, and inclusive. Treat all contributors with decency regardless of experience level.

## How to contribute

### Report a bug

Bug reports are filed as [GitHub issues](https://github.com/ramirocrc/odys/issues/new/choose).

When reporting a bug, include the output of this command so we can reproduce the problem:

```bash
python -c "from importlib.metadata import version; print(version('odys'))"
```

For security vulnerabilities, see [SECURITY.md](SECURITY.md) instead.

### Suggest a feature

Feature requests and general questions can also be filed as [issues](https://github.com/ramirocrc/odys/issues/new/choose).

For non-trivial changes, open an issue first to discuss the approach before submitting a PR.

### Improve documentation

Read [DOCS_GUIDELINES.md](DOCS_GUIDELINES.md) before writing. Every page should have runnable examples and follow the Diátaxis framework.

## Development setup

Make sure you have the following installed:

- **Python 3.11 to 3.14**
- [**uv**](https://docs.astral.sh/uv/) for dependency management
- [**just**](https://github.com/casey/just) for running development commands
- [**git**](https://git-scm.com/) for version control

Fork the repository on GitHub and clone your fork locally.

```bash
# Clone your fork and cd into the repo directory
git clone git@github.com:<your username>/odys.git
cd odys

# Install dependencies and prek hooks
just install
```

## Development workflow

### Create a branch

```bash
git switch -c my-new-feature-branch
# Make your changes...
```

### Run checks before committing

Run these commands before opening a PR. They must all pass.

```bash
# Formatting, linting, and type checking
just check
```

This runs prek hooks plus three type checkers in parallel: `ty`, `pyrefly`, and `basedpyright`. It also checks for obsolete dependencies with `deptry`.

```bash
# Unit tests with coverage
just test
```

Tests require **90% minimum coverage**. If your changes drop coverage below this threshold, add more tests.

```bash
# Documentation build (if you touched docs)
just docs-test
```

```bash
# Integration tests across Python versions
just nox
```

### Commit your changes

Write clear, descriptive commit messages explaining what changed and why.

```bash
git add .
git commit -m "Your detailed description of your changes."
git push origin my-new-feature-branch
```

### Open a pull request

Open a pull request on GitHub. Link any related issues and describe what your changes do.

## Pull Request checklist

Before opening a PR, verify that your changes:

1. Include tests for any new or changed behaviour.
2. Update documentation if they add new functionality.
3. Pass `just check` (formatting, linting, type checking).
4. Pass `just test` with 90%+ coverage.
5. Pass `just docs-test` if you touched documentation.
6. Follow the code style conventions below.
7. Use type hints everywhere with `X | None` syntax, not `Optional[X]`.

## Code style

Follow these conventions to keep the codebase consistent:

- **Type hints everywhere** — use `X | None` union syntax, not `Optional[X]`
- **Pydantic frozen models** — use `ConfigDict(frozen=True, extra="forbid")` for all data classes
- **Custom exceptions** — never raise generic `ValueError` or `TypeError`:
  - `OdysError` — base exception
  - `OdysValidationError` — user input validation failures
  - `OdysSolverError` — solver failures or unexpected status
  - `OdysNoResultsError` — accessing results that don't exist
- **Line length**: 120 characters
- **Docstrings**: Google-style
- **No comments** — split into functions if you need comments to explain sections
- **Test data** — use module-level constants (e.g., `STANDARD_GENERATOR_POWER = 100.0`)

## Project structure

```
src/odys/              # Main package source
tests/unit/            # Unit tests
tests/integration/     # Integration tests (run with `just nox`)
tests/smoke_test.py    # Post-build smoke test
examples/*.py          # Standalone example scripts
docs/                  # Documentation source
```

## Key libraries

- **linopy** — xarray-based linear/mixed-integer optimization modeling
- **highspy** — HiGHS MILP solver (via linopy)
- **xarray** — N-dimensional arrays (scenarios, time, assets dimensions)
- **pydantic** — data validation and immutable models

## Next steps

- Browse [open issues](https://github.com/ramirocrc/odys/issues) to find something to work on
- Read [AGENTS.md](AGENTS.md) for detailed architecture and development guidelines
- Check out the [user guide](https://ramirocrc.github.io/odys/) to understand how Odys works
