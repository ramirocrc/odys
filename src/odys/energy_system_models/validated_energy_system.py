"""Energy system conditions and data structures.

This module provides classes for representing energy system conditions,
including demand profiles and system configurations.
"""

from collections.abc import Sequence
from datetime import timedelta
from functools import cached_property
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from odys._math_model.model_components.parameters.battery_parameters import BatteryParameters
from odys._math_model.model_components.parameters.generator_parameters import GeneratorParameters
from odys._math_model.model_components.parameters.load_parameters import LoadParameters
from odys._math_model.model_components.parameters.market_parameters import MarketParameters
from odys._math_model.model_components.parameters.parameters import (
    EnergySystemParameters,
)
from odys._math_model.model_components.parameters.scenario_parameters import ScenarioParameters
from odys.energy_system_models.assets.generator import PowerGenerator
from odys.energy_system_models.assets.portfolio import AssetPortfolio
from odys.energy_system_models.markets import EnergyMarket
from odys.energy_system_models.scenarios import (
    Scenario,
    StochasticScenario,
    validate_sequence_of_stochastic_scenarios,
)
from odys.energy_system_models.units import PowerUnit
from odys.utils.logging import get_logger

logger = get_logger(__name__)


class ValidatedEnergySystem(BaseModel):
    """Represents the complete energy system configuration with validation.

    This class defines the energy system including the asset portfolio,
    demand profile, time discretization, and available capacity profiles.
    It performs comprehensive validation to ensure the system is feasible:

    - Validates that capacity profile lengths match demand profile length.
    - Ensures available capacity profiles are only specified for generators.
    - Verifies that maximum available power can meet peak demand.
    - Checks that total energy capacity can meet total energy demand.

    Raises:
        ValueError: If the system configuration is infeasible.
        TypeError: If available capacity is specified for non-generator assets.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, extra="forbid")

    portfolio: AssetPortfolio
    timestep: timedelta
    number_of_steps: int
    power_unit: PowerUnit
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
            generators=self._generator_parameters,
            batteries=self._battery_parameters,
            loads=self._load_parameters,
            markets=self._market_parameters,
            scenarios=self._scenario_parameters,
        )

    @cached_property
    def _scenario_parameters(self) -> ScenarioParameters:
        generators_index = self._generator_parameters.index if self._generator_parameters else None
        batteries_index = self._battery_parameters.index if self._battery_parameters else None
        loads_index = self._load_parameters.index if self._load_parameters else None
        markets_index = self._market_parameters.index if self._market_parameters else None

        return ScenarioParameters(
            number_of_timesteps=self.number_of_steps,
            scenarios=self._collection_of_scenarios,
            generators_index=generators_index,
            batteries_index=batteries_index,
            loads_index=loads_index,
            markets_index=markets_index,
        )

    @property
    def _generator_parameters(self) -> GeneratorParameters | None:
        if len(self.portfolio.generators) == 0:
            return None
        return GeneratorParameters(generators=self.portfolio.generators)

    @property
    def _battery_parameters(self) -> BatteryParameters | None:
        if len(self.portfolio.batteries) == 0:
            return None
        return BatteryParameters(self.portfolio.batteries)

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
        self._validate_load_consistent_with_scenario_load_profiles()
        self._validate_markets_consistent_with_scenario_market_prices()

        for scenario in self._collection_of_scenarios:
            self._validate_available_capacity_scenario(scenario)
            self._validate_load_profiles(scenario)

            if not self.markets:
                self._validate_enough_power_to_meet_demand(scenario)
                self._validate_enough_energy_to_meet_demand(scenario)

        return self

    def _validate_load_consistent_with_scenario_load_profiles(self) -> None:
        """Validate consistency between portfolio loads and scenario load profiles.

        If there are loads in the portfolio, each scenario must have a profile for each load.
        If there are no loads in the portfolio, all scenarios should have load_profiles=None.

        Raises:
            ValueError: If load profiles are inconsistent with portfolio loads.
        """
        has_loads = bool(self.portfolio.loads)

        for scenario in self._collection_of_scenarios:
            if has_loads:
                if scenario.load_profiles is None:
                    msg = (
                        f"Portfolio contains loads {[load.name for load in self.portfolio.loads]}, "
                        f"but scenario '{scenario.name}' has no load profiles."
                    )
                    raise ValueError(msg)

                portfolio_load_names = {load.name for load in self.portfolio.loads}
                scenario_load_names = set(scenario.load_profiles.keys())

                missing_loads = portfolio_load_names - scenario_load_names
                if missing_loads:
                    msg = f"Scenario '{scenario.name}' is missing load profiles for: {sorted(missing_loads)}"
                    raise ValueError(msg)

                extra_loads = scenario_load_names - portfolio_load_names
                if extra_loads:
                    msg = (
                        f"Scenario '{scenario.name}' has load profiles for loads not in portfolio: "
                        f"{sorted(extra_loads)}"
                    )
                    raise ValueError(msg)
            elif scenario.load_profiles is not None:
                msg = (
                    f"Portfolio contains no loads, but scenario '{scenario.name}' "
                    f"has load profiles: {list(scenario.load_profiles.keys())}"
                )
                raise ValueError(msg)

    def _validate_markets_consistent_with_scenario_market_prices(self) -> None:
        """Validate consistency between portfolio markets and scenario market prices.

        If there are markets in the portfolio, each scenario must have prices for each market.
        If there are no markets in the portfolio, all scenarios should have market_prices=None.

        Raises:
            ValueError: If market prices are inconsistent with portfolio markets.
        """
        has_markets = bool(self._collection_of_markets)

        for scenario in self._collection_of_scenarios:
            if has_markets:
                if scenario.market_prices is None:
                    msg = (
                        f"Portfolio contains markets {[market.name for market in self._collection_of_markets]}, "
                        f"but scenario '{scenario.name}' has no market prices."
                    )
                    raise ValueError(msg)

                portfolio_market_names = {market.name for market in self._collection_of_markets}
                scenario_market_names = set(scenario.market_prices.keys())

                missing_markets = portfolio_market_names - scenario_market_names
                if missing_markets:
                    msg = f"Scenario '{scenario.name}' is missing market prices for: {sorted(missing_markets)}"
                    raise ValueError(msg)

                extra_markets = scenario_market_names - portfolio_market_names
                if extra_markets:
                    msg = (
                        f"Scenario '{scenario.name}' has market prices for markets not in portfolio: "
                        f"{sorted(extra_markets)}"
                    )
                    raise ValueError(msg)
            elif scenario.market_prices is not None:
                msg = (
                    f"Portfolio contains no markets, but scenario '{scenario.name}' "
                    f"has market prices: {list(scenario.market_prices.keys())}"
                )
                raise ValueError(msg)

    def _validate_load_profiles(self, scenario: Scenario) -> None:
        """Validate that available capacity profiles are only for generators.

        Raises:
            TypeError: If available capacity is specified for non-generator assets.
            ValueError: If capacity profile length doesn't match demand profile.

        """
        if scenario.load_profiles is None:
            return

        for load_name, load_profile in scenario.load_profiles.items():
            if len(load_profile) != self.number_of_steps:
                msg = (
                    f"Length of load profile {load_name} ({len(load_profile)})"
                    f" does not match the number of time steps ({self.number_of_steps})."
                )
                raise ValueError(msg)

    def _validate_available_capacity_scenario(self, scenario: Scenario) -> None:
        """Validate that available capacity profiles are only for generators.

        Raises:
            TypeError: If available capacity is specified for non-generator assets.
            ValueError: If capacity profile length doesn't match demand profile.

        """
        if scenario.available_capacity_profiles is None:
            return

        for asset_name, capacity_profile in scenario.available_capacity_profiles.items():
            asset = self.portfolio.get_asset(asset_name)
            if not isinstance(asset, PowerGenerator):
                msg = (
                    "Available capacity can only be specified for generators, "
                    f"but got '{asset_name}' of type {type(asset)}."
                )
                raise TypeError(msg)
            if len(capacity_profile) != self.number_of_steps:
                msg = (
                    f"Length of capacity profile for {asset_name} ({len(capacity_profile)})"
                    f" does not match the number of time steps ({self.number_of_steps})."
                )
                raise ValueError(msg)
            for capacity_i in capacity_profile:
                if not (0 <= capacity_i <= asset.nominal_power):
                    msg = (
                        f"Available capacity value {capacity_i} for asset '{asset_name}' is invalid. "
                        f"Values must be between 0 and the asset's nominal power ({asset.nominal_power})."
                    )
                    raise ValueError(msg)

    def _validate_enough_power_to_meet_demand(self, scenario: StochasticScenario) -> None:
        """Validate that maximum available power can meet peak demand.

        This method checks that the sum of generator nominal power and
        battery capacity can meet the maximum demand at any time period.

        Raises:
            ValueError: If maximum available power is insufficient for peak demand.

        """
        if scenario.load_profiles is None:
            msg = "Load profile is empty, there is nothing to balance."
            raise ValueError(msg)

        cumulative_generators_power = sum(gen.nominal_power for gen in self.portfolio.generators)
        # TODO: We assume full capacity can be discharged -> Needs to be limited by max power
        cumulative_battery_capacities = sum(bat.capacity for bat in self.portfolio.batteries)
        max_available_power = cumulative_generators_power + cumulative_battery_capacities

        for load_name, load_profile in scenario.load_profiles.items():
            for t, demand_t in enumerate(load_profile):
                if max_available_power < demand_t:
                    msg = (
                        f"Infeasible problem in scenario '{scenario.name}' for load '{load_name}' at time index {t}: "
                        f"Demand = {demand_t}, but maximum available generation + battery = {max_available_power}."
                    )
                    raise ValueError(msg)

    def _validate_enough_energy_to_meet_demand(self, scenario: StochasticScenario) -> None:  # noqa: ARG002
        """Validate that the system has enough energy to meet total demand.

        This method checks that the total energy available from generators
        and batteries can meet the total energy demand over the time horizon.

        """
        # TODO: Validate that:
        # sum(demand * timestep) <= sum(generator.nominal_power * timestep) + sum(battery.soc_initial - battery.soc_terminal) # noqa: ERA001, E501
        return
