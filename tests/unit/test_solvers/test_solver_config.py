"""Tests for the SolverConfig class."""

from typing import cast

import pytest
from pydantic import ValidationError

from odys.solvers.solver_config import SolverConfig, SolverName

VALID_TIME_LIMIT = 10.0
VALID_MIP_REL_GAP = 0.05
VALID_THREADS = 4


def test_default_solver_config() -> None:
    """Default SolverConfig matches expected defaults."""
    config = SolverConfig()
    assert config.solver_name == SolverName.HIGHS
    assert config.time_limit is None
    assert config.mip_rel_gap is None
    assert config.presolve is False
    assert config.threads is None
    assert config.log_output is False
    assert config.solver_options is None


def test_solver_name_enum() -> None:
    """SolverConfig accepts a SolverName enum."""
    config = SolverConfig(solver_name=SolverName.GUROBI)
    assert config.solver_name == SolverName.GUROBI


def test_solver_name_empty_raises() -> None:
    """Empty solver name raises a validation error."""
    with pytest.raises((ValueError, TypeError), match="solver_name"):
        SolverConfig(solver_name=cast("SolverName", ""))


@pytest.mark.parametrize("time_limit", [-1.0, 0.0])
def test_time_limit_not_positive_raises(time_limit: float) -> None:
    """A non-positive time_limit raises a validation error."""
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        SolverConfig(time_limit=time_limit)


def test_time_limit_positive_passes() -> None:
    """A positive time_limit is accepted."""
    config = SolverConfig(time_limit=VALID_TIME_LIMIT)
    assert config.time_limit == VALID_TIME_LIMIT


def test_mip_rel_gap_below_zero_raises() -> None:
    """A mip_rel_gap below 0 raises a validation error."""
    with pytest.raises(ValidationError, match="Input should be greater than or equal to 0"):
        SolverConfig(mip_rel_gap=-0.1)


def test_mip_rel_gap_above_one_raises() -> None:
    """A mip_rel_gap above 1 raises a validation error."""
    with pytest.raises(ValidationError, match="Input should be less than or equal to 1"):
        SolverConfig(mip_rel_gap=1.1)


@pytest.mark.parametrize("mip_rel_gap", [0.0, 1.0])
def test_mip_rel_gap_boundaries_pass(mip_rel_gap: float) -> None:
    """mip_rel_gap is accepted at its inclusive boundaries, 0 and 1."""
    config = SolverConfig(mip_rel_gap=mip_rel_gap)
    assert config.mip_rel_gap == mip_rel_gap


def test_mip_rel_gap_between_zero_and_one_passes() -> None:
    """A mip_rel_gap strictly between 0 and 1 is accepted."""
    config = SolverConfig(mip_rel_gap=VALID_MIP_REL_GAP)
    assert config.mip_rel_gap == VALID_MIP_REL_GAP


@pytest.mark.parametrize("threads", [-1, 0])
def test_threads_not_positive_raises(threads: int) -> None:
    """A non-positive threads value raises a validation error."""
    with pytest.raises(ValidationError, match="Input should be greater than 0"):
        SolverConfig(threads=threads)


def test_threads_positive_passes() -> None:
    """A positive threads value is accepted."""
    config = SolverConfig(threads=VALID_THREADS)
    assert config.threads == VALID_THREADS
