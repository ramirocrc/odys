"""Tests that the code gains no new lint or type-check suppressions.

The Definition of Done in AGENTS.md forbids new escape hatches. ALLOWED_ESCAPE_HATCHES lists the ones
that exist today: a change that adds one fails here, and a change that removes one must lower its
count, so the list only shrinks. Raising a count needs a maintainer's approval in review.
"""

import re
from collections import Counter
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
SCANNED_DIRECTORIES = ("src", "tests", "examples", "docs")
SCANNED_FILES = ("noxfile.py",)
SOURCE_DIRECTORY = "src"

ESCAPE_HATCHES: dict[str, re.Pattern[str]] = {
    "# noqa": re.compile(r"#\s*noqa\b"),
    "# ruff: noqa": re.compile(r"#\s*ruff:\s*noqa\b"),
    "# type: ignore": re.compile(r"#\s*type:\s*ignore"),
    "# pyright: ignore": re.compile(r"#\s*pyright:\s*ignore"),
    "# pyright: mode or rule override": re.compile(r"#\s*pyright:\s*(basic|standard|report\w+\s*=\s*false)"),
    "# mypy: ignore-errors": re.compile(r"#\s*mypy:\s*ignore-errors"),
    "no_type_check": re.compile(r"\bno_type_check\b"),
    "# pyrefly: ignore": re.compile(r"#\s*pyrefly:\s*ignore"),
    "# ty: ignore": re.compile(r"#\s*ty:\s*ignore"),
    "# complexipy: ignore": re.compile(r"#\s*complexipy:\s*ignore"),
    "# pragma: no cover": re.compile(r"#\s*pragma:\s*no\s*cover"),
    "# fmt: off/skip": re.compile(r"#\s*fmt:\s*(off|skip)"),
    "typing.Any": re.compile(r"\btyping\.Any\b|from typing import[^\n]*\bAny\b|[:\[,]\s*Any\b|->\s*Any\b"),
    "cast(...)": re.compile(r"\bcast\("),
    "pytest skip/xfail": re.compile(r"pytest\.(mark\.)?(skip|skipif|xfail)\b"),
    "ignored warning": re.compile(r"(filterwarnings|simplefilter)\(\s*['\"]ignore"),
}
SOURCE_ONLY_ESCAPE_HATCHES: dict[str, re.Pattern[str]] = {
    "raise ValueError/TypeError": re.compile(r"\braise\s+(ValueError|TypeError)\b"),
}

ALLOWED_ESCAPE_HATCHES: dict[tuple[str, str], int] = {
    ("docs/generate_example_plots.py", "# pyrefly: ignore"): 6,
    ("src/odys/domain/entities/base.py", "# pyright: ignore"): 1,
    ("src/odys/optimization/constraints/constraints_group.py", "# noqa"): 1,
    ("src/odys/optimization/constraints/constraints_group.py", "typing.Any"): 2,
    ("src/odys/solvers/config_translators.py", "typing.Any"): 11,
    ("src/odys/solvers/solver_config.py", "typing.Any"): 2,
    ("tests/integration/test_ev_fleet_optimization.py", "# type: ignore"): 3,
    ("tests/smoke_test.py", "# noqa"): 1,
    ("tests/unit/test_domain/entities/test_battery.py", "typing.Any"): 9,
    ("tests/unit/test_domain/entities/test_charger.py", "typing.Any"): 5,
    ("tests/unit/test_domain/entities/test_electric_vehicle.py", "typing.Any"): 13,
    ("tests/unit/test_domain/entities/test_generator.py", "cast(...)"): 1,
    ("tests/unit/test_domain/entities/test_generator.py", "typing.Any"): 2,
    ("tests/unit/test_domain/entities/test_trip.py", "typing.Any"): 7,
    ("tests/unit/test_optimization/formulations/test_charging_formulation.py", "# noqa"): 2,
    ("tests/unit/test_optimization/formulations/test_electric_vehicle_formulation.py", "# noqa"): 1,
    ("tests/unit/test_optimization/formulations/test_generator_formulation.py", "# pyrefly: ignore"): 2,
    ("tests/unit/test_solvers/test_option_translators.py", "typing.Any"): 2,
    ("tests/unit/test_solvers/test_solver.py", "cast(...)"): 1,
    ("tests/unit/test_solvers/test_solver_config.py", "cast(...)"): 1,
}


def _escape_hatches_in(text: str, *, in_source: bool) -> Counter[str]:
    patterns = ESCAPE_HATCHES | SOURCE_ONLY_ESCAPE_HATCHES if in_source else ESCAPE_HATCHES
    counts = Counter({label: len(pattern.findall(text)) for label, pattern in patterns.items()})
    return +counts


def _scanned_python_files() -> list[Path]:
    files = [path for directory in SCANNED_DIRECTORIES for path in (REPOSITORY_ROOT / directory).rglob("*.py")]
    files += [REPOSITORY_ROOT / name for name in SCANNED_FILES]
    this_file = Path(__file__).resolve()
    return sorted(path for path in files if path.resolve() != this_file)


def _repository_escape_hatches() -> Counter[tuple[str, str]]:
    found: Counter[tuple[str, str]] = Counter()
    for path in _scanned_python_files():
        relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        in_source = relative.startswith(f"{SOURCE_DIRECTORY}/")
        for label, count in _escape_hatches_in(path.read_text(encoding="utf-8"), in_source=in_source).items():
            found[relative, label] = count
    return found


@pytest.mark.parametrize(
    ("line", "label"),
    [
        ("x = 1  # noqa: E501", "# noqa"),
        ("# ruff: noqa: D100", "# ruff: noqa"),
        ("y = f()  # type: ignore[arg-type]", "# type: ignore"),
        ("class A(B):  # pyright: ignore[reportUnsafeMultipleInheritance]", "# pyright: ignore"),
        ("# pyright: basic", "# pyright: mode or rule override"),
        ("# pyright: reportMissingImports=false", "# pyright: mode or rule override"),
        ("# mypy: ignore-errors", "# mypy: ignore-errors"),
        ("@no_type_check", "no_type_check"),
        ("z = g()  # pyrefly: ignore[bad-argument-type]", "# pyrefly: ignore"),
        ("z = g()  # ty: ignore[invalid-argument-type]", "# ty: ignore"),
        ("def h():  # complexipy: ignore", "# complexipy: ignore"),
        ("if debug:  # pragma: no cover", "# pragma: no cover"),
        ("# fmt: off", "# fmt: off/skip"),
        ("from typing import Any, ClassVar", "typing.Any"),
        ("def f(x: Any) -> None: ...", "typing.Any"),
        ("def f() -> Any: ...", "typing.Any"),
        ("options: dict[str, Any] = {}", "typing.Any"),
        ("value = cast(int, raw)", "cast(...)"),
        ("@pytest.mark.skip(reason='slow')", "pytest skip/xfail"),
        ("@pytest.mark.xfail", "pytest skip/xfail"),
        ("pytest.skip('no solver')", "pytest skip/xfail"),
        ("@pytest.mark.filterwarnings('ignore::DeprecationWarning')", "ignored warning"),
        ("warnings.simplefilter('ignore')", "ignored warning"),
    ],
    ids=lambda value: value,
)
def test_escape_hatches_in_counts_each_kind(line: str, label: str) -> None:
    assert _escape_hatches_in(line, in_source=False) == Counter({label: 1})


@pytest.mark.parametrize(("in_source", "expected"), [(True, 1), (False, 0)], ids=["source", "elsewhere"])
def test_escape_hatches_in_counts_generic_errors_only_in_source(*, in_source: bool, expected: int) -> None:
    hatches = _escape_hatches_in("raise ValueError(msg)", in_source=in_source)

    assert hatches["raise ValueError/TypeError"] == expected


@pytest.mark.parametrize(
    "line",
    [
        "# A note about noqa comments in prose",
        "class AnyProfile: ...",
        "def broadcast(values): ...",
        "raise OdysValidationError(msg) from err",
    ],
    ids=["prose", "name containing Any", "name ending in cast", "odys error"],
)
def test_escape_hatches_in_ignores_lookalikes(line: str) -> None:
    assert _escape_hatches_in(line, in_source=True) == Counter()


def test_code_adds_no_escape_hatches() -> None:
    allowed = Counter(ALLOWED_ESCAPE_HATCHES)
    added = _repository_escape_hatches() - allowed

    assert not added, (
        f"New escape hatches {dict(added)}. Fix the underlying problem instead (see the Definition of Done in "
        "AGENTS.md); if one is unavoidable, raise its count in ALLOWED_ESCAPE_HATCHES and explain why in the PR."
    )


def test_allowed_escape_hatches_are_still_used() -> None:
    removed = Counter(ALLOWED_ESCAPE_HATCHES) - _repository_escape_hatches()

    assert not removed, f"Escape hatches removed {dict(removed)}. Lower their counts in ALLOWED_ESCAPE_HATCHES."
