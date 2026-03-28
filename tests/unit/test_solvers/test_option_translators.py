"""Tests for per-solver option translators."""

from odys.solvers.option_translators import translate_options

ALL_COMMON_OPTIONS = {
    "time_limit": 120.0,
    "mip_rel_gap": 0.05,
    "presolve": False,
    "threads": 8,
    "log_output": True,
}

DEFAULTS_ONLY = {
    "presolve": True,
    "log_output": False,
}


def test_highs_all_options() -> None:
    """HiGHS translator maps all common options correctly."""
    result = translate_options("highs", ALL_COMMON_OPTIONS)
    assert result == {
        "time_limit": 120.0,
        "mip_rel_gap": 0.05,
        "presolve": "off",
        "threads": 8,
        "output_flag": True,
    }


def test_highs_defaults() -> None:
    """HiGHS translator with defaults only."""
    result = translate_options("highs", DEFAULTS_ONLY)
    assert result == {"presolve": "on", "output_flag": False}


def test_gurobi_all_options() -> None:
    """Gurobi translator maps all common options correctly."""
    result = translate_options("gurobi", ALL_COMMON_OPTIONS)
    assert result == {
        "TimeLimit": 120.0,
        "MIPGap": 0.05,
        "Presolve": 0,
        "Threads": 8,
        "OutputFlag": 1,
    }


def test_gurobi_defaults() -> None:
    """Gurobi translator with defaults only."""
    result = translate_options("gurobi", DEFAULTS_ONLY)
    assert result == {"Presolve": 1, "OutputFlag": 0}


def test_cplex_all_options() -> None:
    """CPLEX translator maps all common options correctly."""
    result = translate_options("cplex", ALL_COMMON_OPTIONS)
    assert result == {
        "timelimit": 120.0,
        "mip.tolerances.mipgap": 0.05,
        "preprocessing.presolve": 0,
        "threads": 8,
        "output.clonelog": 1,
    }


def test_cplex_defaults() -> None:
    """CPLEX translator with defaults only."""
    result = translate_options("cplex", DEFAULTS_ONLY)
    assert result == {"preprocessing.presolve": 1, "output.clonelog": 0}


def test_scip_all_options() -> None:
    """SCIP translator maps all common options correctly."""
    result = translate_options("scip", ALL_COMMON_OPTIONS)
    assert result == {
        "limits/time": 120.0,
        "limits/gap": 0.05,
        "presolving/maxrounds": 0,
        "parallel/maxnthreads": 8,
        "display/verblevel": 4,
    }


def test_scip_defaults() -> None:
    """SCIP translator with defaults only."""
    result = translate_options("scip", DEFAULTS_ONLY)
    assert result == {"presolving/maxrounds": -1, "display/verblevel": 0}


def test_glpk_all_options() -> None:
    """GLPK translator maps all common options correctly."""
    result = translate_options("glpk", ALL_COMMON_OPTIONS)
    assert result == {
        "tmlim": 120.0,
        "mipgap": 0.05,
        "presolve": False,
    }


def test_glpk_defaults() -> None:
    """GLPK translator with defaults only."""
    result = translate_options("glpk", DEFAULTS_ONLY)
    assert result == {"presolve": True}


def test_unknown_solver_passthrough() -> None:
    """Unknown solver passes common options through unchanged."""
    common = {"time_limit": 60.0, "presolve": True, "log_output": False}
    result = translate_options("some_future_solver", common)
    assert result == common
