"""Solver configuration for energy system optimization."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SolverConfig(BaseModel):
    """Configuration for optimization solvers.

    Controls solver selection, common behavior like time limits and optimality
    gaps, and allows raw solver-specific options for advanced use cases.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    solver_name: str = Field(default="highs", min_length=1, description="Linopy solver name.")
    time_limit: float | None = Field(default=None, gt=0, description="Max solve time in seconds.")
    mip_rel_gap: float | None = Field(default=None, ge=0, le=1, description="Relative MIP gap tolerance.")
    presolve: bool = Field(default=True, description="Enable solver presolve.")
    threads: int | None = Field(default=None, gt=0, description="Number of solver threads.")
    log_output: bool = Field(default=False, description="Display solver output logs.")
    solver_options: dict[str, Any] | None = Field(
        default=None,
        description="Raw solver-specific options. Override translated common options.",
    )
