---
icon: lucide/alert-triangle
---

# `odys.domain.exceptions`

Custom exception hierarchy. All exceptions inherit from `OdysError`.

- `OdysError` — Base exception for the library
- `OdysValidationError` — Raised when input validation fails
- `OdysSolverError` — Raised when the solver fails or returns an unexpected status
- `OdysNoResultsError` — Raised when accessing results that don't exist

::: odys.domain.exceptions
