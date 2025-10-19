"""Energy system conditions and data structures.

This module provides classes for representing energy system conditions,
including demand profiles and system configurations.
"""

from collections.abc import Sequence
from datetime import timedelta
from functools import cached_property
from typing import Self

import xarray as xr
from pydantic import BaseModel, Field, field_validator, model_validator

from optimes._math_model.model_components.parameters import (
    BatteryParameters,
    EnergyModelParameters,
    GeneratorParameters,
    LoadParameters,
    MarketParameters,
    ScenarioParameters,
)
from optimes._math_model.model_components.sets import (
    BatteryIndex,
    GeneratorIndex,
    LoadIndex,
    MarketIndex,
    ScenarioIndex,
    TimeIndex,
)
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.markets import EnergyMarket
from optimes.energy_system_models.scenarios import (
    Scenario,
    StochasticScenario,
    validate_sequence_of_stochastic_scenarios,
)
from optimes.energy_system_models.units import PowerUnit
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class ValidatedEnergySystem(BaseModel, frozen=True, arbitrary_types_allowed=True, extra="forbid"):
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

    portfolio: AssetPortfolio
    timestep: timedelta
    number_of_steps: int
    power_unit: PowerUnit
    markets: EnergyMarket | Sequence[EnergyMarket] | None = Field(default=None, init_var=True)
    scenarios: Scenario | Sequence[StochasticScenario] = Field(init_var=True)
    enforce_non_anticipativity: bool = False

    @field_validator("scenarios", mode="after")
    @classmethod
    def _validated_scenario_sequence(
        cls,
        value: Scenario | list[StochasticScenario],
    ) -> Scenario | list[StochasticScenario]:
        if isinstance(value, list):
            validate_sequence_of_stochastic_scenarios(value)

        return value

    @cached_property
    def _collection_of_scenarios(self) -> tuple[StochasticScenario, ...]:
        if isinstance(self.scenarios, Sequence):
            return tuple(self.scenarios)

        return (
            StochasticScenario(
                name="deterministic_scenario",
                probability=1.0,
                available_capacity_profiles=self.scenarios.available_capacity_profiles,
                load_profiles=self.scenarios.load_profiles,
                market_prices=self.scenarios.market_prices,
            ),
        )

    @cached_property
    def _collection_of_markets(self) -> tuple[EnergyMarket, ...]:
        if not self.markets:
            return ()
        if isinstance(self.markets, Sequence):
            return tuple(self.markets)

        return (self.markets,)

    @cached_property
    def _scenario_index(self) -> ScenarioIndex:
        return ScenarioIndex(
            values=tuple(scenario.name for scenario in self._collection_of_scenarios),
        )

    @cached_property
    def _time_index(self) -> TimeIndex:
        return TimeIndex(
            values=tuple(str(time_step) for time_step in range(self.number_of_steps)),
        )

    @cached_property
    def _generator_index(self) -> GeneratorIndex:
        return GeneratorIndex(
            values=tuple(gen.name for gen in self.portfolio.generators),
        )

    @cached_property
    def _battery_index(self) -> BatteryIndex:
        return BatteryIndex(
            values=tuple(battery.name for battery in self.portfolio.batteries),
        )

    @cached_property
    def _load_index(self) -> LoadIndex:
        return LoadIndex(
            values=tuple(load.name for load in self.portfolio.loads),
        )

    @cached_property
    def _market_index(self) -> MarketIndex:
        return MarketIndex(
            values=tuple(market.name for market in self._collection_of_markets),
        )

    @cached_property
    def parameters(self) -> EnergyModelParameters:
        """Returns energy model parameters."""
        return EnergyModelParameters(
            generators=GeneratorParameters(
                index=self._generator_index,
                nominal_power=self._generators_nominal_power,
                variable_cost=self._generators_variable_cost,
                min_up_time=self._generators_min_up_time,
                min_power=self._generators_min_power,
                startup_cost=self._generators_startup_cost,
                max_ramp_up=self._generators_max_ramp_up,
                max_ramp_down=self._generators_max_ramp_down,
            ),
            batteries=BatteryParameters(
                index=self._battery_index,
                capacity=self._batteries_capacity,
                max_power=self._batteries_max_power,
                efficiency_charging=self._batteries_efficiency_charging,
                efficiency_discharging=self._batteries_efficiency_discharging,
                soc_start=self._batteries_soc_start,
                soc_end=self._batteries_soc_end,
                soc_min=self._batteries_soc_min,
                soc_max=self._batteries_soc_max,
            ),
            loads=LoadParameters(
                index=self._load_index,
            ),
            markets=MarketParameters(
                index=self._market_index,
            ),
            system=ScenarioParameters(
                scenario_index=self._scenario_index,
                time_index=self._time_index,
                enforce_non_anticipativity=self.enforce_non_anticipativity,
                load_profiles=self._load_profiles,
                market_prices=self._market_prices,
                available_capacity_profiles=self._available_capacity_profiles,
                scenario_probabilities=self._scenario_probabilities,
            ),
        )

    @model_validator(mode="after")
    def _validate_inputs(self) -> Self:
        """Validate all system inputs after model creation.

        This validator ensures that the energy system configuration
        is feasible and consistent.

        Returns:
            Self if validation passes.

        Raises:
            ValueError: If the system configuration is infeasible.

        """
        self._validate_load_consisten_with_scenario_load_profiles()
        self._validate_markets_consistent_with_scenario_market_prices()

        for scenario in self._collection_of_scenarios:
            self._validate_available_capacity_scenario(scenario)
            self._validate_load_profiles(scenario)

            if not self.markets:
                self._validate_enough_power_to_meet_demand(scenario)
                self._validate_enough_energy_to_meet_demand(scenario)

        return self

    def _validate_load_consisten_with_scenario_load_profiles(self) -> None:
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

    def _validate_enough_energy_to_meet_demand(self, scenario: StochasticScenario) -> None:
        """Validate that the system has enough energy to meet total demand.

        This method checks that the total energy available from generators
        and batteries can meet the total energy demand over the time horizon.

        """
        # TODO: Validate that:
        # sum(demand * timestep) <= sum(generator.nominal_power * timestep) + sum(battery.soc_initial - battery.soc_terminal) # noqa: ERA001, E501

    @property
    def _generators_nominal_power(self) -> xr.DataArray:
        return xr.DataArray(
            data=[gen.nominal_power for gen in self.portfolio.generators],
            coords=self._generator_index.coordinates,
        )

    @property
    def _generators_variable_cost(self) -> xr.DataArray:
        return xr.DataArray(
            data=[gen.variable_cost for gen in self.portfolio.generators],
            coords=self._generator_index.coordinates,
        )

    @property
    def _generators_min_up_time(self) -> xr.DataArray:
        return xr.DataArray(
            data=[gen.min_up_time for gen in self.portfolio.generators],
            coords=self._generator_index.coordinates,
        )

    @property
    def _generators_min_power(self) -> xr.DataArray:
        return xr.DataArray(
            data=[gen.min_power for gen in self.portfolio.generators],
            coords=self._generator_index.coordinates,
        )

    @property
    def _generators_startup_cost(self) -> xr.DataArray:
        return xr.DataArray(
            data=[gen.startup_cost for gen in self.portfolio.generators],
            coords=self._generator_index.coordinates,
        )

    @property
    def _generators_max_ramp_up(self) -> xr.DataArray:
        return xr.DataArray(
            data=[gen.ramp_up for gen in self.portfolio.generators],
            coords=self._generator_index.coordinates,
        )

    @property
    def _generators_max_ramp_down(self) -> xr.DataArray:
        return xr.DataArray(
            data=[gen.ramp_down for gen in self.portfolio.generators],
            coords=self._generator_index.coordinates,
        )

    @property
    def _batteries_capacity(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.capacity for battery in self.portfolio.batteries],
            coords=self._battery_index.coordinates,
        )

    @property
    def _batteries_max_power(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.max_power for battery in self.portfolio.batteries],
            coords=self._battery_index.coordinates,
        )

    @property
    def _batteries_efficiency_charging(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.efficiency_charging for battery in self.portfolio.batteries],
            coords=self._battery_index.coordinates,
        )

    @property
    def _batteries_efficiency_discharging(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.efficiency_discharging for battery in self.portfolio.batteries],
            coords=self._battery_index.coordinates,
        )

    @property
    def _batteries_soc_start(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.soc_start for battery in self.portfolio.batteries],
            coords=self._battery_index.coordinates,
        )

    @property
    def _batteries_soc_end(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.soc_end for battery in self.portfolio.batteries],
            coords=self._battery_index.coordinates,
        )

    @property
    def _batteries_soc_min(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.soc_min for battery in self.portfolio.batteries],
            coords=self._battery_index.coordinates,
        )

    @property
    def _batteries_soc_max(self) -> xr.DataArray:
        batteries_soc_max = []
        for battery in self.portfolio.batteries:
            battery_soc_max = battery.soc_max if battery.soc_max else battery.capacity
            batteries_soc_max.append(battery_soc_max)
        return xr.DataArray(
            data=batteries_soc_max,
            coords=self._battery_index.coordinates,
        )

    @property
    def _load_profiles(self) -> xr.DataArray | None:
        if not self.portfolio.loads:
            return None
        all_load_profiles = []
        for scenario in self._collection_of_scenarios:
            scenario_load_profiles_mapping = scenario.load_profiles or {}
            scenario_load_profiles_array = [
                scenario_load_profiles_mapping.get(load.name) for load in self.portfolio.loads
            ]
            all_load_profiles.append(scenario_load_profiles_array)

        return xr.DataArray(
            data=all_load_profiles,
            coords=self._scenario_index.coordinates | self._load_index.coordinates | self._time_index.coordinates,
        )

    @property
    def _market_prices(self) -> xr.DataArray | None:
        if not self.markets:
            return None
        all_market_prices = []
        for scenario in self._collection_of_scenarios:
            scenario_market_prices_mapping = scenario.market_prices or {}
            scenario_market_prices_array = [
                scenario_market_prices_mapping.get(market.name) for market in self._collection_of_markets
            ]
            all_market_prices.append(scenario_market_prices_array)

        return xr.DataArray(
            data=all_market_prices,
            coords=self._scenario_index.coordinates | self._market_index.coordinates | self._time_index.coordinates,
        )

    @property
    def _available_capacity_profiles(self) -> xr.DataArray:
        all_capacity_profiles = []

        for scenario in self._collection_of_scenarios:
            profiles = scenario.available_capacity_profiles or {}
            scenario_complete_capacity_profiles = [
                profiles.get(gen.name, [gen.nominal_power] * self.number_of_steps) for gen in self.portfolio.generators
            ]
            all_capacity_profiles.append(scenario_complete_capacity_profiles)

        return xr.DataArray(
            data=all_capacity_profiles,
            coords=self._scenario_index.coordinates | self._generator_index.coordinates | self._time_index.coordinates,
        )

    @property
    def _scenario_probabilities(self) -> xr.DataArray:
        """Returns scenario probabilities as xarray DataArray."""
        return xr.DataArray(
            data=[scenario.probability for scenario in self._collection_of_scenarios],
            coords=self._scenario_index.coordinates,
        )
