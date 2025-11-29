install:
    @echo "🚀 Creating virtual environment using uv"
    uv sync --python 3.14 --all-groups
    uv run pre-commit install

precommit-refresh:
    @echo "🚀 Refreshing pre-commit hooks"
    uv run pre-commit autoupdate
    uv run pre-commit clean
    uv run pre-commit install

check:
    @echo "🚀 Checking lock file consistency with 'pyproject.toml'"
    uv lock --locked
    @echo "🚀 Linting code: Running pre-commit"
    uv run pre-commit run -a
    @echo "🚀 Static type checking: Running pyright"
    uv run pyright src tests
    @echo "🚀 Checking for obsolete dependencies: Running deptry"
    uv run deptry src

test:
    @echo "🚀 Testing code: Running pytest"
    uv run python -m pytest -n auto --cov-report term-missing:skip-covered --cov=src tests/ --durations=10

clean-build:
    @echo "🚀 Removing build artifacts"
    uv run python -c "import shutil, os; shutil.rmtree('dist') if os.path.exists('dist') else None"

build: clean-build
    @echo "🚀 Creating wheel file"
    uvx --from build pyproject-build --installer uv

publish:
    @echo "🚀 Publishing."
    uvx twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

build-and-publish: build publish

docs-test:
    @echo "🚀 Testing docs build"
    uv run mkdocs build -s

docs:
    @echo "🚀 Serving docs"
    uv run mkdocs serve

nox:
    @echo "🚀 Launching nox sessions"
    uvx nox
