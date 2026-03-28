"""Solver configuration for energy system optimization."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SolverConfig(BaseModel):
    """Configuration for the HiGHS solver.

    Controls solver behavior like time limits, optimality gaps, and verbosity.
    All fields have sensible defaults that work for most use cases.

    Args:
        time_limit: Maximum solve time in seconds. None means no limit.
        mip_rel_gap: Relative MIP optimality gap tolerance (0.0 = prove optimality).
        presolve: Whether to enable HiGHS presolve.
        threads: Number of threads for the solver. None means solver default.
        log_output: Whether to display solver output logs.

    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    time_limit: float | None = Field(default=None, gt=0, description="Max solve time in seconds.")
    mip_rel_gap: float | None = Field(default=None, ge=0, le=1, description="Relative MIP gap tolerance.")
    presolve: bool = Field(default=True, description="Enable HiGHS presolve.")
    threads: int | None = Field(default=None, gt=0, description="Number of solver threads.")
    log_output: bool = Field(default=False, description="Display solver output logs.")

    def to_solver_options(self) -> dict[str, Any]:
        """Convert to a dict of HiGHS solver options for linopy's ``Model.solve()``.

        Excludes ``None`` values so solver defaults aren't overridden.
        Renames ``log_output`` to ``output_flag`` and converts ``presolve``
        to the "on"/"off" strings HiGHS expects.
        """
        options = self.model_dump(exclude_none=True)
        options["presolve"] = "on" if options.pop("presolve") else "off"
        options["output_flag"] = options.pop("log_output")
        return options
