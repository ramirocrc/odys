"""Solver configuration for energy system optimization."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from odys.solvers.option_translators import translate_options


class SolverConfig(BaseModel):
    """Configuration for optimization solvers.

    Controls solver selection, common behavior like time limits and optimality
    gaps, and allows raw solver-specific options for advanced use cases.

    Args:
        solver_name: Name of the solver to use. Must be available in linopy.
        time_limit: Maximum solve time in seconds. None means no limit.
        mip_rel_gap: Relative MIP optimality gap tolerance (0.0 = prove optimality).
        presolve: Whether to enable solver presolve.
        threads: Number of threads for the solver. None means solver default.
        log_output: Whether to display solver output logs.
        solver_options: Raw solver-specific options that override any translated
            common options. Passed directly to linopy's ``Model.solve()``.

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

    def to_solver_options(self) -> dict[str, Any]:
        """Convert to a dict of solver-specific options for linopy's ``Model.solve()``.

        Translates common options (time_limit, presolve, etc.) into the format
        expected by the configured solver. Any entries in ``solver_options``
        take precedence over the translated values.
        """
        common = self.model_dump(
            include={"time_limit", "mip_rel_gap", "threads"},
            exclude_none=True,
        )
        common["presolve"] = self.presolve
        common["log_output"] = self.log_output

        translated = translate_options(self.solver_name, common)

        if self.solver_options is not None:
            translated.update(self.solver_options)

        return translated
