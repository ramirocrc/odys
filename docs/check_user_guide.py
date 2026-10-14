"""Check that every User Guide page runs and prints what it says it prints.

Usage:
    uv run --locked python docs/check_user_guide.py

The Python blocks of each page run in order, in one namespace per page, so a block can use the
names of the blocks above it on the same page but nothing from other pages. When a `text` block
directly follows a Python block, it must match what that block printed, ignoring column spacing
and the sign of zero. The docs build fails otherwise, so an example that stops running or a solve
that changes shows up before publishing.
"""

import contextlib
import io
import re
import runpy
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import NamedTuple

USER_GUIDE = Path(__file__).resolve().parent / "user_guide"
SIGNED_ZERO = re.compile(r"(?<![\w.])-(0(?:\.0*)?)(?![\w.])")
FENCE = re.compile(
    r"^(?P<indent>[ \t]*)```(?P<language>python|text)\n(?P<body>.*?)^(?P=indent)```[ \t]*$",
    re.DOTALL | re.MULTILINE,
)


class Block(NamedTuple):
    """One fenced code block of a page."""

    language: str
    body: str
    line: int
    start: int
    end: int


class UserGuideBlockError(Exception):
    """A Python block of the User Guide raised an error."""


def _blocks(text: str) -> Iterator[Block]:
    for match in FENCE.finditer(text):
        indent = match.group("indent")
        body = "\n".join(line.removeprefix(indent) for line in match.group("body").splitlines())
        line = text.count("\n", 0, match.start()) + 1
        yield Block(match.group("language"), body, line, match.start(), match.end())


def _normalized(text: str) -> str:
    """Return `text` without what a solver may change between equal solutions: column spacing and the sign of zero."""
    return "\n".join(SIGNED_ZERO.sub(r"\1", " ".join(line.split())) for line in text.strip("\n").splitlines())


def _shows_output_of(previous: Block | None, block: Block, text: str) -> bool:
    return previous is not None and not text[previous.end : block.start].strip()


def _run(code: str, namespace: dict[str, object], script: Path) -> str:
    script.write_text(code, encoding="utf-8")
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        namespace.update(runpy.run_path(str(script), init_globals=namespace))
    return printed.getvalue()


def check_page(page: Path, workdir: Path) -> list[str]:
    """Run the Python blocks of one page and return its problems.

    Args:
        page: The Markdown page.
        workdir: A directory for the scripts the blocks run from.

    Returns:
        One message per block that printed something other than its `text` block.

    Raises:
        UserGuideBlockError: If a block raises an error, naming the page and line.
    """
    text = page.read_text(encoding="utf-8")
    name = page.relative_to(USER_GUIDE.parent)
    namespace: dict[str, object] = {}
    problems: list[str] = []
    previous: Block | None = None
    printed = ""
    for block in _blocks(text):
        if block.language == "python":
            try:
                printed = _run(block.body, namespace, workdir / f"block_{block.line}.py")
            except Exception as error:
                msg = f"{name}:{block.line}: {type(error).__name__}: {error}"
                raise UserGuideBlockError(msg) from error
        elif _shows_output_of(previous, block, text) and _normalized(block.body) != _normalized(printed):
            problems.append(
                f"{name}:{block.line}: the output differs from what the code above prints:\n"
                f"--- documented\n{_normalized(block.body)}\n--- printed\n{_normalized(printed)}",
            )
        previous = block if block.language == "python" else None
    return problems


def main() -> int:
    """Check every User Guide page.

    Returns:
        The exit code: 0 when every page passes, 1 otherwise.
    """
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as workdir:
        for page in sorted(USER_GUIDE.rglob("*.md")):
            problems.extend(check_page(page, Path(workdir)))
    for problem in problems:
        sys.stderr.write(f"{problem}\n\n")
    sys.stdout.write(f"Checked the User Guide: {len(problems)} problem(s).\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
