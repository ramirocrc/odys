
# justfile equivalent of the provided Makefile

# Install the virtual environment and install the pre-commit hooks
install:
    @echo "🚀 Creating virtual environment using uv"
    uv sync --python 3.13 --all-groups
    uvx pre-commit install

# Run code quality tools
check:
    @echo "🚀 Checking lock file consistency with 'pyproject.toml'"
    uv lock --locked
    @echo "🚀 Linting code: Running pre-commit"
    uv run pre-commit run -a
    @echo "🚀 Static type checking: Running pyright"
    uv run pyright src
    @echo "🚀 Checking for obsolete dependencies: Running deptry"
    uv run deptry src

# Test the code with pytest
test:
    @echo "🚀 Testing code: Running pytest"
    uv run python -m pytest --cov --cov-config=pyproject.toml --cov-report=xml

# Generate test report
test-report:
    @echo "🚀 Generating test report"
    pytest --cov-report term --cov=src tests/

# Clean build artifacts
clean-build:
    @echo "🚀 Removing build artifacts"
    uv run python -c "import shutil, os; shutil.rmtree('dist') if os.path.exists('dist') else None"

# Build wheel file
build: clean-build
    @echo "🚀 Creating wheel file"
    uvx --from build pyproject-build --installer uv

# Publish a release to PyPI
publish:
    @echo "🚀 Publishing."
    uvx twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

# Build and publish
build-and-publish: build publish

# Test if documentation can be built without warnings or errors
docs-test:
    @echo "🚀 Testing docs build"
    uv run mkdocs build -s

# Build and serve the documentation
docs:
    @echo "🚀 Serving docs"
    uv run mkdocs serve

# Launh nox sessions
nox:
    @echo "🚀 Launching nox sessions"
    uvx nox
