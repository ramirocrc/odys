"""Custom exceptions for the odys library."""


class OdysError(Exception):
    """Base exception for the odys library."""


class OdysValidationError(OdysError):
    """Raised when input validation fails."""


class OdysSolverError(OdysError):
    """Raised when the solver fails or returns an unexpected status."""


class OdysNoResultsError(OdysError):
    """Raised when accessing results that don't exist."""
