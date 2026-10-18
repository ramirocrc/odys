"""The Overview of the Mathematical Formulation links every numbered constraint, and only existing ones.

Each constraint page labels its constraints in a heading such as `### G-7 · Output changes gradually {#g-7}`.
The Overview's "whole model on one screen" must link each of them as `generators.md#g-7`, so a new constraint
can't be left out, and every such link must point to a label that exists.
"""

import re
from pathlib import Path

import pytest

FORMULATION_DIR = Path(__file__).parents[2] / "docs" / "formulation"
OVERVIEW = FORMULATION_DIR / "index.md"

CONSTRAINT_HEADING = re.compile(r"^#{2,3} [A-Z]+-\d+ · .*\{#([a-z]+-\d+)\}$", re.MULTILINE)
CONSTRAINT_LINK = re.compile(r"\]\(([a-z_]+\.md)#([a-z]+-\d+)\)")


def _constraint_anchors() -> list[str]:
    return sorted(
        f"{page.name}#{anchor}"
        for page in FORMULATION_DIR.glob("*.md")
        if page != OVERVIEW
        for anchor in CONSTRAINT_HEADING.findall(page.read_text(encoding="utf-8"))
    )


def _overview_links() -> list[str]:
    links = CONSTRAINT_LINK.findall(OVERVIEW.read_text(encoding="utf-8"))
    return sorted({f"{page}#{anchor}" for page, anchor in links})


CONSTRAINT_ANCHORS = _constraint_anchors()
OVERVIEW_LINKS = _overview_links()


def test_formulation_pages_have_constraint_anchors() -> None:
    assert CONSTRAINT_ANCHORS


@pytest.mark.parametrize("anchor", CONSTRAINT_ANCHORS, ids=CONSTRAINT_ANCHORS)
def test_formulation_overview_constraint_anchor_is_linked(anchor: str) -> None:
    assert anchor in OVERVIEW_LINKS


@pytest.mark.parametrize("link", OVERVIEW_LINKS, ids=OVERVIEW_LINKS)
def test_formulation_overview_constraint_link_exists(link: str) -> None:
    assert link in CONSTRAINT_ANCHORS
