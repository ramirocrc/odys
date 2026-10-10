"""Energy system configuration and optimization.

This module provides the EnergySystem class, the main entry point
for configuring and optimizing energy systems. It performs validation
on initialization and provides an optimize() method for solving.
"""

from collections.abc import Sequence
from datetime import timedelta
from functools import cached_property
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from odys.domain.entities.base import EnergyEntity
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.horizon import Horizon
from odys.domain.objective import Objective
from odys.domain.scenario import Scenario, ScenarioSet
from odys.domain.validation import validate_energy_system_inputs
from odys.optimization.formulations import validate_entities_supported
from odys.optimization.model.model_builder import build_model
from odys.optimization.problem import OptimizationProblem
from odys.results.optimization_results import OptimalDispatchResults
from odys.solvers.solver import solve
from odys.solvers.solver_config import SolverConfig


class EnergySystem(BaseModel):
    """Energy system configuration and optimization orchestrator.

    This class provides a high-level interface for configuring and optimizing
    energy systems. It performs comprehensive validation on initialization to ensure
    the system configuration is feasible, then provides an optimize() method
    for solving the optimization problem.

    Validation includes:
    - Validating that the timestep is positive and there is at least one step
    - Validating that scenario probabilities sum to 1 and names are unique
    - Checking that each profile references an asset or market of the system
    - Checking that every load and market has a profile in every scenario
    - Checking that every profile has one value per timestep
    - Checking that electric vehicle trips fit the horizon
    - Ensuring maximum supply can meet minimum demand at every timestep

    Raises:
        OdysValidationError: If the system configuration is invalid or infeasible.

    Example:
        >>> gen = Generator(name="gen1", nominal_power=100, variable_cost=20)
        >>> load = FixedLoad(name="load1")
        >>> portfolio = AssetPortfolio(assets=[gen, load])
        >>> system = EnergySystem(
        ...     portfolio=portfolio,
        ...     timestep=timedelta(hours=1),
        ...     number_of_steps=3,
        ...     scenarios=Scenario(profiles=(LoadProfile(load=load, values=[50, 80, 60]),)),
        ... )
        >>> results = system.optimize()
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, extra="forbid")

    portfolio: AssetPortfolio
    timestep: timedelta
    number_of_steps: int
    objective: Objective = Field(default_factory=Objective)
    markets: EnergyMarket | Sequence[EnergyMarket] | None = Field(default=None, init_var=True)
    scenarios: Scenario | Sequence[Scenario] = Field(init_var=True)

    @model_validator(mode="after")
    def _validate_inputs(self) -> Self:
        validate_entities_supported(self._entities)
        validate_energy_system_inputs(
            portfolio=self.portfolio,
            scenario_set=self.scenario_set,
            markets=self.collection_of_markets,
            horizon=self.horizon,
        )
        return self

    @property
    def horizon(self) -> Horizon:
        """Return the time grid of the optimization."""
        return Horizon(timestep=self.timestep, number_of_steps=self.number_of_steps)

    @cached_property
    def scenario_set(self) -> ScenarioSet:
        """Return the scenarios as a `ScenarioSet`; a single `Scenario` becomes a one-element set."""
        if isinstance(self.scenarios, Scenario):
            return ScenarioSet(scenarios=(self.scenarios,))
        return ScenarioSet(scenarios=tuple(self.scenarios))

    @cached_property
    def collection_of_markets(self) -> tuple[EnergyMarket, ...]:
        """Return markets as a normalized tuple."""
        if self.markets is None:
            return ()
        if isinstance(self.markets, EnergyMarket):
            return (self.markets,)
        return tuple(self.markets)

    @property
    def _entities(self) -> tuple[EnergyEntity, ...]:
        """Return every asset of the portfolio, then every market."""
        return (*self.portfolio.assets.values(), *self.collection_of_markets)

    def build_problem(self) -> OptimizationProblem:
        """Build the optimization problem of this energy system: one formulation per entity type and objective term."""
        return OptimizationProblem.assemble(self._entities, self.horizon, self.scenario_set, self.objective)

    def optimize(self, solver_config: SolverConfig | None = None) -> OptimalDispatchResults:
        """Optimize the energy system.

        This method builds and solves the optimization model using the configured solver.

        Args:
            solver_config: Solver configuration. Uses HiGHS defaults if not provided.

        Returns:
            OptimizationResults containing the solution and metadata.

        """
        problem = self.build_problem()
        outcome = solve(build_model(problem), solver_config or SolverConfig())
        return OptimalDispatchResults(outcome, problem.dispatches)
