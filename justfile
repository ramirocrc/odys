install:
    @echo "🚀 Creating virtual environment using uv"
    uv sync --python 3.14 --all-groups
    uv run --locked pre-commit install

precommit-refresh:
    @echo "🚀 Refreshing pre-commit hooks"
    uv run --locked pre-commit autoupdate
    uv run --locked pre-commit clean
    uv run --locked pre-commit install

check:
    @echo "🚀 Checking lock file consistency with 'pyproject.toml'"
    uv lock --locked
    @echo "🚀 Linting code: Running pre-commit"
    uv run --locked pre-commit run -a
    @echo "🚀 Static type checking: Running pyright"
    uv run --locked pyright src tests
    @echo "🚀 Checking for obsolete dependencies: Running deptry"
    uv run --locked deptry src

test:
    @echo "🚀 Testing code: Running pytest"
    uv run --locked python -m pytest -n auto --cov-report term-missing:skip-covered --cov=src tests/ --durations=10


build:
    @echo "🚀 Removing build artifacts"
    uv run --locked python -c "import shutil, os; shutil.rmtree('dist') if os.path.exists('dist') else None"
    @echo "🚀 Creating wheel file"
    uv build

publish:
    @echo "🚀 Publishing."
    uvx twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

build-and-publish: build publish

docs-test:
    @echo "🚀 Testing docs build"
    uv run --locked mkdocs build -s

docs:
    @echo "🚀 Serving docs"
    uv run --locked mkdocs serve

nox:
    @echo "🚀 Launching nox sessions"
    uvx nox
