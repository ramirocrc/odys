"""Tests that AGENTS.md and the playbooks in .agents/skills stay true to the repository.

Every repository path they name in backticks must exist, the playbook table in AGENTS.md must list
exactly the playbooks that exist, and each playbook's frontmatter must name its own directory.
"""

import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
AGENTS_FILE = REPOSITORY_ROOT / "AGENTS.md"
PLAYBOOKS_DIRECTORY = REPOSITORY_ROOT / ".agents" / "skills"
PLAYBOOK_FILE_NAME = "SKILL.md"
TOP_LEVEL_DIRECTORIES = ("src", "tests", "docs", "tools", "examples", ".agents", ".github")

BACKTICKED = re.compile(r"`([^`\s]+)`")
PLACEHOLDER = re.compile(r"[<>{}*]|\.\.\.")
PLAYBOOK_LINK = re.compile(r"\]\(\.agents/skills/([\w-]+)/SKILL\.md\)")
FRONTMATTER_NAME = re.compile(r"\A---\n(?:.*\n)*?name: ([\w-]+)\n(?:.*\n)*?---\n")


def _guideline_files() -> list[Path]:
    return [AGENTS_FILE, *sorted(PLAYBOOKS_DIRECTORY.glob(f"*/{PLAYBOOK_FILE_NAME}"))]


def _playbook_names() -> list[str]:
    return sorted(path.parent.name for path in PLAYBOOKS_DIRECTORY.glob(f"*/{PLAYBOOK_FILE_NAME}"))


def _repository_paths(text: str) -> set[str]:
    candidates = (match.removesuffix("/") for match in BACKTICKED.findall(text))
    return {
        candidate
        for candidate in candidates
        if candidate.split("/", 1)[0] in TOP_LEVEL_DIRECTORIES
        and "/" in candidate
        and not PLACEHOLDER.search(candidate)
    }


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Mirror `src/odys/domain/entities/flexible_load.py`.", {"src/odys/domain/entities/flexible_load.py"}),
        ("Put it in `tests/unit/`.", {"tests/unit"}),
        ("Add `tests/unit/test_<asset>.py`.", set()),
        ("Read `entities/base.py` and `pyproject.toml`.", set()),
        ("Run `just check`.", set()),
    ],
    ids=["file", "directory", "placeholder", "relative to a package", "command"],
)
def test_repository_paths_reads_only_paths_from_the_repository_root(text: str, expected: set[str]) -> None:
    assert _repository_paths(text) == expected


@pytest.mark.parametrize("guideline", _guideline_files(), ids=lambda path: path.relative_to(REPOSITORY_ROOT).as_posix())
def test_guideline_paths_exist(guideline: Path) -> None:
    paths = _repository_paths(guideline.read_text(encoding="utf-8"))

    missing = sorted(path for path in paths if not (REPOSITORY_ROOT / path).exists())

    assert not missing, f"{guideline.name} names paths that do not exist: {missing}"


def test_agents_file_links_every_playbook() -> None:
    linked = sorted(PLAYBOOK_LINK.findall(AGENTS_FILE.read_text(encoding="utf-8")))

    assert linked == _playbook_names()


@pytest.mark.parametrize("name", _playbook_names())
def test_playbook_frontmatter_names_its_directory(name: str) -> None:
    text = (PLAYBOOKS_DIRECTORY / name / PLAYBOOK_FILE_NAME).read_text(encoding="utf-8")

    match = FRONTMATTER_NAME.match(text)

    assert match is not None, f"{name}/{PLAYBOOK_FILE_NAME} has no frontmatter with a name"
    assert match.group(1) == name
