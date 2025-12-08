install:
    @echo "🚀 Creating virtual environment using uv"
    uv sync --python 3.14 --all-groups
    uv run --locked prek install

precommit-refresh:
    @echo "🚀 Refreshing pre-commit hooks"
    uv run --locked pre-commit autoupdate
    uv run --locked pre-commit clean
    uv run --locked pre-commit install

check:
    @echo "🚀 Checking lock file consistency with 'pyproject.toml'"
    uv sync --locked --all-groups
    @echo "🚀 Linting code: Running pre-commit"
    uv run --locked pre-commit run -a
    @echo "🚀 Static type checking: Running pyright"
    uv run --locked pyright src tests
    @echo "🚀 Checking for obsolete dependencies: Running deptry"
    uv run --locked deptry src

test:
    @echo "🚀 Testing code: Running pytest"
    uv run --locked python -m pytest -n auto --cov-report term-missing:skip-covered --cov=src tests/ --durations=10

nox:
    @echo "🚀 Launching nox sessions"
    uvx nox

build:
    @echo "🚀 Removing build artifacts"
    rm -rf dist/
    @echo "🚀 Building source distribution and wheel"
    uv build --no-sources
    @echo "🚀 Smoke test whell"
    uv run --isolated --no-project --with dist/*.whl tests/smoke_test.py
    @echo "🚀 Smoke test source distribution"
    uv run --isolated --no-project --with dist/*.tar.gz tests/smoke_test.py

publish:
    @echo "🚀 Publishing package"
    uv publish

build-and-publish: build publish

docs:
    @echo "🚀 Serving docs"
    uv run --locked mkdocs serve

docs-test:
    @echo "🚀 Testing docs build"
    uv run --locked mkdocs build --strict

docs-deploy:
    @echo "🚀 Deploying docs"
    uv run --locked mkdocs gh-deploy --force
