"""What a solver run returns: status, termination condition, objective value and solution."""

from enum import StrEnum

import xarray as xr
from pydantic import BaseModel, ConfigDict


class SolveStatus(StrEnum):
    """Status reported by the solver.

    A solution is available only with `OK`, and not always then: a time limit reached before a feasible
    solution is found also reports `OK`. Check `SolveOutcome.has_solution`.
    """

    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    ABORTED = "aborted"
    UNKNOWN = "unknown"


class SolveOutcome(BaseModel):
    """Result of solving a model, independent of the problem it was built from.

    Without a solution, the objective value is `None` and the solution is empty.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    status: SolveStatus
    termination_condition: str
    objective_value: float | None
    solution: xr.Dataset

    @property
    def has_solution(self) -> bool:
        """Whether the solver returned a solution."""
        return self.objective_value is not None
