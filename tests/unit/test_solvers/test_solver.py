"""Tests for the solver module."""

import pytest

from odys.domain.exceptions import OdysSolverError
from odys.solvers.solver import validate_solver_available
from odys.solvers.solver_config import SolverName


def test_validate_solver_available_highs() -> None:
    """HiGHS is installed and passes validation."""
    validate_solver_available(SolverName.HIGHS)


def test_validate_solver_unavailable_raises() -> None:
    """An unavailable solver raises OdysSolverError."""
    with pytest.raises(OdysSolverError, match="not available"):
        validate_solver_available("nonexistent_solver")  # type: ignore[arg-type]
