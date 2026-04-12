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


def test_solver_name_custom() -> None:
    """SolverConfig accepts a custom solver name."""
    config = SolverConfig(solver_name="gurobi")
    assert config.solver_name == "gurobi"


def test_solver_name_empty_raises() -> None:
    """Empty solver name raises a validation error."""
    with pytest.raises((ValueError, TypeError), match="solver_name"):
        SolverConfig(solver_name="")
