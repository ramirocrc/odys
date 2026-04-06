"""Energy system configuration and optimization.

This module provides the EnergySystem class, the main entry point
for configuring and optimizing energy systems. It performs validation
on initialization and provides an optimize() method for solving.
"""

from collections.abc import Sequence
from datetime import timedelta
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.objective import Objective
from odys.domain.scenarios import (
    Scenario,
    StochasticScenario,
    validate_sequence_of_stochastic_scenarios,
)
from odys.domain.units import PowerUnit
from odys.domain.validation import validate_energy_system_inputs
from odys.optimization.model.model_builder import build_model
from odys.optimization.parameters.generator_parameters import GeneratorParameters
from odys.optimization.parameters.load_parameters import LoadParameters
from odys.optimization.parameters.market_parameters import MarketParameters
from odys.optimization.parameters.parameters import EnergySystemParameters
from odys.optimization.parameters.scenario_parameters import ScenarioParameters
from odys.optimization.parameters.storage_parameters import StorageParameters
from odys.results.optimization_results import OptimizationResults
from odys.solvers.solver import optimize_algebraic_model
from odys.solvers.solver_config import SolverConfig


class EnergySystem(BaseModel):
    """Energy system configuration and optimization orchestrator.

    This class provides a high-level interface for configuring and optimizing
    energy systems. It performs comprehensive validation on initialization to ensure
    the system configuration is feasible, then provides an optimize() method
    for solving the optimization problem.

    Validation includes:
    - Validating that scenario probabilities sum to 1
    - Ensuring unique scenario names
    - Validating load profiles match portfolio loads
    - Validating market prices match configured markets
    - Checking capacity profile lengths match time steps
    - Verifying available capacity profiles are only for generators
    - Ensuring maximum available power can meet peak demand

    Raises:
        OdysValidationError: If the system configuration is invalid or infeasible.

    Example:
        >>> gen = Generator(name="gen1", nominal_power=100, variable_cost=20)
        >>> portfolio = AssetPortfolio(generators=[gen])
        >>> system = EnergySystem(
        ...     portfolio=portfolio,
        ...     timestep=timedelta(hours=1),
        ...     number_of_steps=24,
        ...     power_unit="MW",
        ...     scenarios=[Scenario()],
        ... )
        >>> results = system.optimize()
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, extra="forbid")

    portfolio: AssetPortfolio
    timestep: timedelta
    number_of_steps: int
    power_unit: PowerUnit
    objective: Objective = Field(default_factory=Objective)
    markets: EnergyMarket | Sequence[EnergyMarket] | None = Field(default=None, init_var=True)
    scenarios: Scenario | Sequence[StochasticScenario] = Field(init_var=True)

    @field_validator("scenarios", mode="after")
    @staticmethod
    def _validate_scenarios(value: Scenario | list[StochasticScenario]) -> Scenario | list[StochasticScenario]:
        if isinstance(value, list):
            validate_sequence_of_stochastic_scenarios(value)
        return value

    @model_validator(mode="after")
    def _validate_inputs(self) -> Self:
        validate_energy_system_inputs(
            portfolio=self.portfolio,
            scenarios=self.collection_of_scenarios,
            markets=self.collection_of_markets,
            number_of_steps=self.number_of_steps,
        )
        return self

    @property
    def collection_of_scenarios(self) -> tuple[StochasticScenario, ...]:
        """Return scenarios as a normalized tuple.

        If a single deterministic Scenario is provided, it is wrapped in a
        StochasticScenario with probability 1.0.
        """
        if isinstance(self.scenarios, Scenario):
            return (
                StochasticScenario(
                    name="deterministic_scenario",
                    probability=1.0,
                    available_capacity_profiles=self.scenarios.available_capacity_profiles,
                    load_profiles=self.scenarios.load_profiles,
                    market_prices=self.scenarios.market_prices,
                ),
            )
        return tuple(self.scenarios)

    @property
    def collection_of_markets(self) -> tuple[EnergyMarket, ...]:
        """Return markets as a normalized tuple."""
        if not self.markets:
            return ()
        if isinstance(self.markets, EnergyMarket):
            return (self.markets,)
        return tuple(self.markets)

    def build_parameters(self) -> EnergySystemParameters:
        """Build parameters from this energy system for the optimization model."""
        generator_params = GeneratorParameters.from_assets(self.portfolio.generators)
        storage_params = StorageParameters.from_assets(self.portfolio.storages)
        load_params = LoadParameters.from_assets(self.portfolio.loads)
        market_params = MarketParameters.from_assets(self.collection_of_markets)

        scenario_params = ScenarioParameters(
            number_of_timesteps=self.number_of_steps,
            scenarios=self.collection_of_scenarios,
            generators_index=generator_params.index if generator_params else None,
            storages_index=storage_params.index if storage_params else None,
            loads_index=load_params.index if load_params else None,
            markets_index=market_params.index if market_params else None,
        )

        return EnergySystemParameters(
            timestep=self.timestep,
            generators=generator_params,
            storages=storage_params,
            loads=load_params,
            markets=market_params,
            scenarios=scenario_params,
            objective=self.objective,
        )

    def optimize(self, solver_config: SolverConfig | None = None) -> OptimizationResults:
        """Optimize the energy system.

        This method builds and solves the optimization model using the configured solver.

        Args:
            solver_config: Solver configuration. Uses HiGHS defaults if not provided.

        Returns:
            OptimizationResults containing the solution and metadata.

        """
        params = self.build_parameters()
        milp_model = build_model(params)
        return optimize_algebraic_model(
            milp_model=milp_model,
            solver_config=solver_config,
        )
