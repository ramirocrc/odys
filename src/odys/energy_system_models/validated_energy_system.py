"""Validated energy system configuration.

This module provides the ValidatedEnergySystem class which validates
and transforms user-provided energy system configurations into
parameters suitable for the optimization model.
"""

from collections.abc import Sequence
from datetime import timedelta
from functools import cached_property
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.markets import EnergyMarket
from odys.energy_system_models.scenarios import (
    Scenario,
    StochasticScenario,
    validate_sequence_of_stochastic_scenarios,
)
from odys.energy_system_models.units import PowerUnit
from odys.energy_system_models.validation import validate_energy_system_inputs
from odys.math_model.model_components.parameters.generator_parameters import GeneratorParameters
from odys.math_model.model_components.parameters.load_parameters import LoadParameters
from odys.math_model.model_components.parameters.market_parameters import MarketParameters
from odys.math_model.model_components.parameters.parameters import (
    EnergySystemParameters,
)
from odys.math_model.model_components.parameters.scenario_parameters import ScenarioParameters
from odys.math_model.model_components.parameters.storage_parameters import StorageParameters
from odys.optimization.objective import Objective


class ValidatedEnergySystem(BaseModel):
    """Represents the complete energy system configuration with validation.

    This class defines the energy system including the asset portfolio,
    demand profile, time discretization, and available capacity profiles.
    It performs comprehensive validation to ensure the system is feasible:

    - Validates that capacity profile lengths match demand profile length
    - Ensures available capacity profiles are only specified for generators
    - Verifies that maximum available power can meet peak demand
    - Checks that total energy capacity can meet total energy demand

    Raises:
        ValueError: If the system configuration is infeasible.
        TypeError: If available capacity is specified for non-generator assets.
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
    def _validated_scenario_sequence(
        value: Scenario | list[StochasticScenario],
    ) -> Scenario | list[StochasticScenario]:
        if isinstance(value, list):
            validate_sequence_of_stochastic_scenarios(value)

        return value

    @cached_property
    def _collection_of_scenarios(self) -> tuple[StochasticScenario, ...]:
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

    @cached_property
    def _collection_of_markets(self) -> tuple[EnergyMarket, ...]:
        if not self.markets:
            return ()
        if isinstance(self.markets, EnergyMarket):
            return (self.markets,)

        return tuple(self.markets)

    @cached_property
    def energy_system_parameters(self) -> EnergySystemParameters:
        """Parameters of the energy system."""
        return EnergySystemParameters(
            timestep=self.timestep,
            generators=self._generator_parameters,
            storages=self._storage_parameters,
            loads=self._load_parameters,
            markets=self._market_parameters,
            scenarios=self._scenario_parameters,
            objective=self.objective,
        )

    @cached_property
    def _scenario_parameters(self) -> ScenarioParameters:
        generators_index = self._generator_parameters.index if self._generator_parameters else None
        storages_index = self._storage_parameters.index if self._storage_parameters else None
        loads_index = self._load_parameters.index if self._load_parameters else None
        markets_index = self._market_parameters.index if self._market_parameters else None

        return ScenarioParameters(
            number_of_timesteps=self.number_of_steps,
            scenarios=self._collection_of_scenarios,
            generators_index=generators_index,
            storages_index=storages_index,
            loads_index=loads_index,
            markets_index=markets_index,
        )

    @property
    def _generator_parameters(self) -> GeneratorParameters | None:
        if len(self.portfolio.generators) == 0:
            return None
        return GeneratorParameters(generators=self.portfolio.generators)

    @property
    def _storage_parameters(self) -> StorageParameters | None:
        if len(self.portfolio.storages) == 0:
            return None
        return StorageParameters(self.portfolio.storages)

    @property
    def _load_parameters(self) -> LoadParameters | None:
        if len(self.portfolio.loads) == 0:
            return None
        return LoadParameters(loads=self.portfolio.loads)

    @property
    def _market_parameters(self) -> MarketParameters | None:
        if self.markets is None:
            return None
        return MarketParameters(self._collection_of_markets)

    @model_validator(mode="after")
    def _validate_inputs(self) -> Self:
        validate_energy_system_inputs(
            portfolio=self.portfolio,
            scenarios=self._collection_of_scenarios,
            markets=self._collection_of_markets,
            number_of_steps=self.number_of_steps,
        )
        return self
