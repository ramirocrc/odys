"""Validated energy system configuration.

This module provides the ValidatedEnergySystem class which validates
user-provided energy system configurations.
"""

from collections.abc import Sequence
from datetime import timedelta
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
        OdysValidationError: If the system configuration is infeasible.

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

    @model_validator(mode="after")
    def _validate_inputs(self) -> Self:
        validate_energy_system_inputs(
            portfolio=self.portfolio,
            scenarios=self.collection_of_scenarios,
            markets=self.collection_of_markets,
            number_of_steps=self.number_of_steps,
        )
        return self
