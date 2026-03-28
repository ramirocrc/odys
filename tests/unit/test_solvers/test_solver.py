"""Tests for the solver module."""

import pytest

from odys.exceptions import OdysSolverError
from odys.solvers.solver import _validate_solver_available


def test_validate_solver_available_highs() -> None:
    """HiGHS is installed and passes validation."""
    _validate_solver_available("highs")


def test_validate_solver_unavailable_raises() -> None:
    """An unavailable solver raises OdysSolverError."""
    with pytest.raises(OdysSolverError, match="not available"):
        _validate_solver_available("nonexistent_solver")
