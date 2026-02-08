# Contributing to odys

Contributions to odys are welcome and appreciated!

## Issues

Bug reports, feature requests and general questions can all be filed as [issues](https://github.com/ramirocrc/odys/issues/new/choose).

When reporting a bug, please include the output of the following call so we can reproduce the problem:

```bash
python -c "from importlib.metadata import version; print(version('odys'))"
```

## Pull Requests

Getting started with a pull request is straightforward.

For non-trivial changes, please open an issue first to discuss the approach before submitting a PR.

### Prerequisites

Make sure you have the following installed:

- **Python 3.11 to 3.14**
- [**uv**](https://docs.astral.sh/uv/) for dependency management
- [**just**](https://github.com/casey/just) for running development commands
- [**git**](https://git-scm.com/) for version control

### Installation and setup

Fork the repository on GitHub and clone your fork locally.

```bash
# Clone your fork and cd into the repo directory
git clone git@github.com:ramirocrc/odys.git
cd odys

# Install dependencies and prek hooks
just install
```

### Check out a new branch and make your changes

```bash
git switch -c my-new-feature-branch
# Make your changes...
```

### Run tests and linting

Before opening a PR, verify that formatting, linting and tests all pass locally.

```bash
# Run automated code formatting and linting
just check

# Run tests
just test
```

### Build documentation

If your changes touch documentation, verify the build still succeeds.

```bash
just docs-test
```

### Commit and push your changes

Once everything passes, commit and push your branch.

```bash
git add .
git commit -m "Your detailed description of your changes."
git push origin my-new-feature-branch
```

Then open a pull request on GitHub. Link any related issues and describe what your changes do.

## Pull Request Guidelines

Please make sure your pull request:

1. Includes tests for any new or changed behaviour.
2. Updates documentation if it adds new functionality.
