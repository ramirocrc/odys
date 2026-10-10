"""Tests that the class diagrams in docs/architecture/model.md stay true to the code in src/odys."""

import ast
import re
from collections import Counter
from collections.abc import Iterator, Mapping
from functools import cache
from pathlib import Path
from typing import NamedTuple

import pytest

import odys

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SOURCE_ROOT = REPOSITORY_ROOT / "src" / "odys"
ARCHITECTURE_PAGE = REPOSITORY_ROOT / "docs" / "architecture" / "model.md"

EXTENSION_POINT_BASES = (
    "EnergyEntity",
    "Profile",
    "ObjectiveTerm",
    "Formulation",
    "ObjectiveTermFormulation",
    "Dispatch",
)
CORE_PIPELINE_CLASSES = (
    "ScenarioSet",
    "Horizon",
    "OperatingConditions",
    "ModelContext",
    "Coordinates",
    "ModelDimension",
    "EntityArrays",
    "FormulationInputs",
    "ObjectiveTermInputs",
    "StorageFormulation",
    "OptimizationProblem",
    "PowerBalance",
    "ConstraintGroup",
    "VariableOwner",
    "SolveOutcome",
)

MERMAID_BLOCK = re.compile(r"^```mermaid\n(.*?)^```", re.MULTILINE | re.DOTALL)
GENERIC = r"(?:~[^~]*~)?"
CLASS_DECLARATION = re.compile(rf"^class\s+(\w+){GENERIC}\s*(\{{)?\s*$")
RELATION = re.compile(
    rf'^(\w+){GENERIC}\s*(?:"[^"]*"\s*)?(<\|--|--\|>|\*--|o--|-->|\.\.>|\.\.\|>|<\|\.\.|--)\s*(?:"[^"]*"\s*)?(\w+){GENERIC}\s*(?::.*)?$',
)
MEMBER = re.compile(r"^\+(\w+)")
IGNORED_LINE = re.compile(r"^(?:<<.*>>|%%.*|direction\s+\w+)?$")


class SourceClass(NamedTuple):
    """A class defined in src/odys: the names of its bases and of its own members."""

    bases: tuple[str, ...]
    members: frozenset[str]


class Inheritance(NamedTuple):
    """A `Base <|-- Subclass` edge drawn in a diagram."""

    base: str
    subclass: str


class ClassDiagrams(NamedTuple):
    """What the class diagrams of the page state about the code."""

    classes: frozenset[str]
    members: Mapping[str, frozenset[str]]
    inheritance: tuple[Inheritance, ...]
    unparsed: tuple[str, ...]


def _base_name(base: ast.expr) -> str:
    if isinstance(base, ast.Subscript):
        return _base_name(base.value)
    if isinstance(base, ast.Attribute):
        return base.attr
    return ast.unparse(base)


def _member_names(statement: ast.stmt) -> Iterator[str]:
    if isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name):
        yield statement.target.id
    elif isinstance(statement, ast.Assign):
        yield from (target.id for target in statement.targets if isinstance(target, ast.Name))
    elif isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef):
        yield statement.name


@cache
def _source_class_definitions() -> tuple[tuple[str, SourceClass], ...]:
    return tuple(
        (
            node.name,
            SourceClass(
                bases=tuple(_base_name(base) for base in node.bases),
                members=frozenset(name for statement in node.body for name in _member_names(statement)),
            ),
        )
        for path in sorted(SOURCE_ROOT.rglob("*.py"))
        for node in ast.parse(path.read_text(encoding="utf-8")).body
        if isinstance(node, ast.ClassDef)
    )


@cache
def _source_classes() -> Mapping[str, SourceClass]:
    return dict(_source_class_definitions())


def _ancestors(name: str) -> frozenset[str]:
    classes = _source_classes()
    if name not in classes:
        return frozenset()
    bases = tuple(base for base in classes[name].bases if base != name)
    return frozenset(bases).union(*(_ancestors(base) for base in bases))


def _members_with_inherited(name: str) -> frozenset[str]:
    classes = _source_classes()
    return frozenset().union(*(classes[owner].members for owner in {name, *_ancestors(name)} if owner in classes))


def _required_classes() -> frozenset[str]:
    public = {name for name in odys.__all__ if name in _source_classes()}
    extension_points = {name for name in _source_classes() if set(EXTENSION_POINT_BASES) & (_ancestors(name) | {name})}
    return frozenset(public | extension_points | set(CORE_PIPELINE_CLASSES))


def _lines_with_owner(lines: list[str]) -> Iterator[tuple[str | None, str]]:
    owner: str | None = None
    for line in lines:
        if owner is not None and line == "}":
            owner = None
            continue
        yield owner, line
        if owner is None and (declaration := CLASS_DECLARATION.match(line)) and declaration.group(2):
            owner = declaration.group(1)


def _inheritance(left: str, arrow: str, right: str) -> Inheritance | None:
    match arrow:
        case "<|--":
            return Inheritance(base=left, subclass=right)
        case "--|>":
            return Inheritance(base=right, subclass=left)
        case _:
            return None


def _parse_class_diagram(lines: list[str]) -> ClassDiagrams:
    classes: set[str] = set()
    members: dict[str, set[str]] = {}
    inheritance: list[Inheritance] = []
    unparsed: list[str] = []
    for owner, line in _lines_with_owner(lines):
        if owner is not None and (member := MEMBER.match(line)):
            members.setdefault(owner, set()).add(member.group(1))
        elif owner is None and (declaration := CLASS_DECLARATION.match(line)):
            classes.add(declaration.group(1))
        elif owner is None and (relation := RELATION.match(line)):
            left, arrow, right = relation.groups()
            classes.update((left, right))
            if edge := _inheritance(left, arrow, right):
                inheritance.append(edge)
        elif not IGNORED_LINE.match(line):
            unparsed.append(line)
    return ClassDiagrams(
        classes=frozenset(classes),
        members={name: frozenset(names) for name, names in members.items()},
        inheritance=tuple(inheritance),
        unparsed=tuple(unparsed),
    )


def parse_class_diagrams(markdown: str) -> ClassDiagrams:
    """Collect the class names, `+member` names and inheritance edges of every classDiagram block.

    Only `+` members are read, so every member on the page is public and checked. Any other line except
    stereotypes (`<<abstract>>`), `%%` comments and `direction` is returned in `unparsed`, so syntax the check
    does not understand fails the test instead of escaping it.
    """
    diagrams = [
        _parse_class_diagram(lines[1:])
        for block in MERMAID_BLOCK.findall(markdown)
        if (lines := [line.strip() for line in block.splitlines()]) and lines[0] == "classDiagram"
    ]
    members: dict[str, frozenset[str]] = {}
    for diagram in diagrams:
        for name, names in diagram.members.items():
            members[name] = members.get(name, frozenset()) | names
    return ClassDiagrams(
        classes=frozenset().union(*(diagram.classes for diagram in diagrams)),
        members=members,
        inheritance=tuple(edge for diagram in diagrams for edge in diagram.inheritance),
        unparsed=tuple(line for diagram in diagrams for line in diagram.unparsed),
    )


@cache
def _page_diagrams() -> ClassDiagrams:
    return parse_class_diagrams(ARCHITECTURE_PAGE.read_text(encoding="utf-8"))


def test_source_class_names_are_unique() -> None:
    duplicates = sorted(
        name for name, count in Counter(name for name, _ in _source_class_definitions()).items() if count > 1
    )

    assert not duplicates, f"The diagram check resolves classes by name; these are defined more than once: {duplicates}"


def test_diagrams_use_only_syntax_the_check_understands() -> None:
    unparsed = _page_diagrams().unparsed

    assert not unparsed, f"Rewrite these diagram lines in a form the drift check parses: {list(unparsed)}"


def test_diagrams_show_every_public_and_core_model_class() -> None:
    missing = sorted(_required_classes() - _page_diagrams().classes)

    assert not missing, f"Add these classes to a classDiagram in {ARCHITECTURE_PAGE.name}: {missing}"


def test_diagrams_name_only_classes_defined_in_the_code() -> None:
    unknown = sorted(_page_diagrams().classes - _source_classes().keys())

    assert not unknown, f"These diagram classes are not defined in src/odys (renamed or removed?): {unknown}"


def test_diagram_inheritance_edges_match_the_code() -> None:
    wrong = [edge for edge in _page_diagrams().inheritance if edge.base not in _ancestors(edge.subclass)]

    assert not wrong, f"These `Base <|-- Subclass` edges do not hold in src/odys: {wrong}"


def test_diagram_members_exist_on_their_class() -> None:
    unknown = {
        name: sorted(names - _members_with_inherited(name))
        for name, names in _page_diagrams().members.items()
        if names - _members_with_inherited(name)
    }

    assert not unknown, f"These diagram members do not exist on their class (or its bases): {unknown}"


@pytest.mark.parametrize(
    ("markdown", "expected"),
    [
        (
            "```mermaid\nclassDiagram\n    class Base {\n        <<abstract>>\n"
            "        +field: int\n        +method() str\n    }\n```\n",
            ClassDiagrams(frozenset({"Base"}), {"Base": frozenset({"field", "method"})}, (), ()),
        ),
        (
            '```mermaid\nclassDiagram\n    Base~T~ <|-- Child\n    Child *-- "0..*" Part : holds\n```\n',
            ClassDiagrams(frozenset({"Base", "Child", "Part"}), {}, (Inheritance("Base", "Child"),), ()),
        ),
        (
            "```mermaid\nclassDiagram\n    Child --|> Base\n```\n",
            ClassDiagrams(frozenset({"Base", "Child"}), {}, (Inheritance("Base", "Child"),), ()),
        ),
        (
            "```mermaid\nclassDiagram\n    class A {\n        +x\n    }\n```\n\n"
            "```mermaid\nclassDiagram\n    class A {\n        +y\n    }\n```\n",
            ClassDiagrams(frozenset({"A"}), {"A": frozenset({"x", "y"})}, (), ()),
        ),
        (
            '```mermaid\nclassDiagram\n    class A["label"]\n    class B {\n        -hidden\n    }\n```\n',
            ClassDiagrams(frozenset({"B"}), {}, (), ('class A["label"]', "-hidden")),
        ),
        (
            "```mermaid\nsequenceDiagram\n    class Ignored\n```\n",
            ClassDiagrams(frozenset(), {}, (), ()),
        ),
    ],
    ids=[
        "class-body-members",
        "relations-and-generics",
        "right-pointing-inheritance",
        "members-merged-across-diagrams",
        "unknown-syntax-reported",
        "non-class-diagram-ignored",
    ],
)
def test_parse_class_diagrams_reads_classes_members_and_inheritance(markdown: str, expected: ClassDiagrams) -> None:
    assert parse_class_diagrams(markdown) == expected
