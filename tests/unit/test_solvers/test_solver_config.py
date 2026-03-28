"""Tests for the SolverConfig class."""

import pytest

from odys.solvers.solver_config import SolverConfig


def test_default_solver_config() -> None:
    """Default SolverConfig matches expected defaults."""
    config = SolverConfig()
    assert config.solver_name == "highs"
    assert config.time_limit is None
    assert config.mip_rel_gap is None
    assert config.presolve is True
    assert config.threads is None
    assert config.log_output is False
    assert config.solver_options is None


def test_to_solver_options_defaults() -> None:
    """Default config produces correct HiGHS solver options dict."""
    options = SolverConfig().to_solver_options()
    assert options == {"presolve": "on", "output_flag": False}


def test_to_solver_options_all_set() -> None:
    """Fully configured SolverConfig produces complete HiGHS solver options dict."""
    config = SolverConfig(
        time_limit=120.0,
        mip_rel_gap=0.05,
        presolve=False,
        threads=8,
        log_output=True,
    )
    options = config.to_solver_options()
    assert options == {
        "time_limit": 120.0,
        "mip_rel_gap": 0.05,
        "presolve": "off",
        "threads": 8,
        "output_flag": True,
    }


def test_solver_name_custom() -> None:
    """SolverConfig accepts a custom solver name."""
    config = SolverConfig(solver_name="gurobi")
    assert config.solver_name == "gurobi"


def test_solver_name_empty_raises() -> None:
    """Empty solver name raises a validation error."""
    with pytest.raises(Exception):  # noqa: B017
        SolverConfig(solver_name="")


def test_solver_options_override() -> None:
    """Raw solver_options override translated common options."""
    config = SolverConfig(
        solver_name="highs",
        presolve=True,
        solver_options={"presolve": "off", "custom_option": 42},
    )
    options = config.to_solver_options()
    assert options["presolve"] == "off"
    assert options["custom_option"] == 42


def test_to_solver_options_gurobi() -> None:
    """SolverConfig with gurobi translates options to Gurobi format."""
    config = SolverConfig(
        solver_name="gurobi",
        time_limit=300.0,
        mip_rel_gap=0.01,
        threads=4,
        presolve=False,
        log_output=True,
    )
    options = config.to_solver_options()
    assert options == {
        "TimeLimit": 300.0,
        "MIPGap": 0.01,
        "Threads": 4,
        "Presolve": 0,
        "OutputFlag": 1,
    }
