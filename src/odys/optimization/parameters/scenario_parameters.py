"""Scenario parameters for the mathematical optimization model."""

from collections.abc import Sequence
from functools import cached_property
from typing import ClassVar

import numpy as np
import xarray as xr

from odys.domain.scenarios import StochasticScenario
from odys.optimization.model.sets import ModelDimension, ModelIndex
from odys.optimization.parameters.flexible_load_parameters import FlexibleLoadIndex
from odys.optimization.parameters.generator_parameters import GeneratorIndex
from odys.optimization.parameters.market_parameters import MarketIndex
from odys.optimization.parameters.storage_parameters import StorageIndex


class TimeIndex(ModelIndex):
    """Index for time components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Time


class ScenarioIndex(ModelIndex):
    """Index for scenario components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Scenarios


class ScenarioParameters:
    """Parameters for scenarios in the energy system model."""

    def __init__(  # noqa: PLR0913
        self,
        number_of_timesteps: int,
        scenarios: Sequence[StochasticScenario],
        generators_index: GeneratorIndex,
        storages_index: StorageIndex,
        markets_index: MarketIndex,
        flexible_loads_index: FlexibleLoadIndex,
    ) -> None:
        """Initialize scenario parameters.

        Args:
            number_of_timesteps: Number of time steps in the scenarios.
            scenarios: Sequence of stochastic scenario objects.
            generators_index: Generator index.
            storages_index: Storage index.
            markets_index: Market index.
            flexible_loads_index: Flexible load index.
        """
        self._number_of_timesteps = number_of_timesteps
        self._scenarios = scenarios
        self._generators_index = generators_index
        self._storages_index = storages_index
        self._markets_index = markets_index
        self._flexible_loads_index = flexible_loads_index
        self._time_index = TimeIndex(values=tuple(str(time_step) for time_step in range(number_of_timesteps)))
        self._scenario_index = ScenarioIndex(values=tuple(scenario.name for scenario in self._scenarios))

    @property
    def time_index(self) -> TimeIndex:
        """Return the time index."""
        return self._time_index

    @property
    def scenario_index(self) -> ScenarioIndex:
        """Return the scenario index."""
        return self._scenario_index

    @cached_property
    def fixed_load_profiles(self) -> xr.DataArray | None:
        """Return fixed load profiles across scenarios and time.

        Note: Fixed loads are not indexed by a model dimension since they have
        no decision variables. They are summed over all fixed loads to produce
        a single profile per scenario-time point.
        """
        has_any_fixed_loads = any(scenario.fixed_load_profiles is not None for scenario in self._scenarios)
        if not has_any_fixed_loads:
            return None

        all_fixed_load_profiles = []
        for scenario in self._scenarios:
            if scenario.fixed_load_profiles is None:
                profile = [0.0] * self._number_of_timesteps
            else:
                profile = [0.0] * self._number_of_timesteps
                for load_profile in scenario.fixed_load_profiles.values():
                    for t in range(self._number_of_timesteps):
                        profile[t] += load_profile[t]
            all_fixed_load_profiles.append(profile)

        return xr.DataArray(
            data=all_fixed_load_profiles,
            coords=self._scenario_index.coordinates | self._time_index.coordinates,
        )

    @cached_property
    def flexible_load_base_profiles(self) -> xr.DataArray | None:
        """Return flexible load base profiles across scenarios and time."""
        has_any_flexible_loads = any(scenario.flexible_load_base_profiles is not None for scenario in self._scenarios)
        if not has_any_flexible_loads:
            return None

        all_load_profiles = []
        for scenario in self._scenarios:
            scenario_load_profiles_mapping = scenario.flexible_load_base_profiles or {}
            scenario_load_profiles_array = [
                scenario_load_profiles_mapping.get(load_name) for load_name in self._flexible_loads_index.values
            ]
            all_load_profiles.append(scenario_load_profiles_array)

        return xr.DataArray(
            data=all_load_profiles,
            coords=(
                self._scenario_index.coordinates | self._flexible_loads_index.coordinates | self._time_index.coordinates
            ),
        )

    @cached_property
    def market_prices(self) -> xr.DataArray | None:
        """Return market prices across scenarios and time."""
        if self._markets_index.is_empty:
            return None
        all_market_prices = []
        for scenario in self._scenarios:
            scenario_market_prices_mapping = scenario.market_prices or {}
            scenario_market_prices_array = [
                scenario_market_prices_mapping.get(market_name) for market_name in self._markets_index.values
            ]
            all_market_prices.append(scenario_market_prices_array)

        return xr.DataArray(
            data=all_market_prices,
            coords=self._scenario_index.coordinates | self._markets_index.coordinates | self._time_index.coordinates,
        )

    @cached_property
    def available_capacity_profiles(self) -> xr.DataArray | None:
        """Return available capacity profiles for generators across scenarios and time."""
        if self._generators_index.is_empty:
            return None
        all_capacity_profiles = []

        for scenario in self._scenarios:
            profiles = scenario.available_capacity_profiles or {}
            scenario_complete_capacity_profiles = [
                profiles.get(gen_name, [np.inf] * self._number_of_timesteps)
                for gen_name in self._generators_index.values
            ]
            all_capacity_profiles.append(scenario_complete_capacity_profiles)

        return xr.DataArray(
            data=all_capacity_profiles,
            coords=self._scenario_index.coordinates | self._generators_index.coordinates | self._time_index.coordinates,
        )

    @cached_property
    def scenario_probabilities(self) -> xr.DataArray:
        """Returns scenario probabilities as xarray DataArray."""
        return xr.DataArray(
            data=[scenario.probability for scenario in self._scenarios],
            coords=self._scenario_index.coordinates,
        )
