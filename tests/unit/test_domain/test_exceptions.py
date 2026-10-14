"""Tests for custom exceptions in the odys library."""

import pytest

import odys
from odys.domain.exceptions import (
    OdysError,
    OdysNoResultsError,
    OdysSolverError,
    OdysValidationError,
)

TEST_MESSAGE = "test message"
VALIDATION_MESSAGE = "validation failed"
SOLVER_MESSAGE = "solver failed"
NO_RESULTS_MESSAGE = "no results available"


class TestOdysError:
    def test_base_exception_inherits_from_exception(self) -> None:
        assert issubclass(OdysError, Exception)

    def test_can_raise_and_catch_odys_error(self) -> None:
        with pytest.raises(OdysError):
            raise OdysError(TEST_MESSAGE)

    def test_exception_contains_message(self) -> None:
        msg = "custom error message"
        with pytest.raises(OdysError, match=msg):
            raise OdysError(msg)


class TestOdysValidationError:
    def test_inherits_from_odys_error(self) -> None:
        assert issubclass(OdysValidationError, OdysError)

    def test_can_raise_and_catch_odys_validation_error(self) -> None:
        with pytest.raises(OdysValidationError):
            raise OdysValidationError(VALIDATION_MESSAGE)

    def test_can_catch_as_odys_error(self) -> None:
        with pytest.raises(OdysError):
            raise OdysValidationError(VALIDATION_MESSAGE)


class TestOdysSolverError:
    def test_inherits_from_odys_error(self) -> None:
        assert issubclass(OdysSolverError, OdysError)

    def test_can_raise_and_catch_odys_solver_error(self) -> None:
        with pytest.raises(OdysSolverError):
            raise OdysSolverError(SOLVER_MESSAGE)

    def test_can_catch_as_odys_error(self) -> None:
        with pytest.raises(OdysError):
            raise OdysSolverError(SOLVER_MESSAGE)


class TestOdysNoResultsError:
    def test_inherits_from_odys_error(self) -> None:
        assert issubclass(OdysNoResultsError, OdysError)

    def test_can_raise_and_catch_odys_no_results_error(self) -> None:
        with pytest.raises(OdysNoResultsError):
            raise OdysNoResultsError(NO_RESULTS_MESSAGE)

    def test_can_catch_as_odys_error(self) -> None:
        with pytest.raises(OdysError):
            raise OdysNoResultsError(NO_RESULTS_MESSAGE)


class TestExceptionInheritanceHierarchy:
    def test_exception_hierarchy_is_correct(self) -> None:
        assert OdysValidationError.__mro__ == (
            OdysValidationError,
            OdysError,
            Exception,
            BaseException,
            object,
        )
        assert OdysSolverError.__mro__ == (
            OdysSolverError,
            OdysError,
            Exception,
            BaseException,
            object,
        )
        assert OdysNoResultsError.__mro__ == (
            OdysNoResultsError,
            OdysError,
            Exception,
            BaseException,
            object,
        )


@pytest.mark.parametrize(
    "exception",
    [OdysError, OdysValidationError, OdysSolverError, OdysNoResultsError],
    ids=lambda exception: exception.__name__,
)
def test_exception_is_exported_from_odys(exception: type[OdysError]) -> None:
    assert exception.__name__ in odys.__all__
    assert getattr(odys, exception.__name__) is exception
