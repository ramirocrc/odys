"""Scenario parameters for the mathematical optimization model."""

from collections.abc import Sequence
from functools import cached_property

import numpy as np
import xarray as xr

from odys.domain.scenarios import StochasticScenario
from odys.optimization.model.coordinates import CoordinatesStore, ModelCoordinates


class ScenarioParameters:
    """Parameters for scenarios in the energy system model."""

    def __init__(
        self,
        scenarios: Sequence[StochasticScenario],
        coordinates_store: CoordinatesStore,
    ) -> None:
        """Initialize scenario parameters.

        Args:
            scenarios: Sequence of stochastic scenario objects.
            coordinates_store: All model dimension coordinates.
        """
        self._scenarios = scenarios
        self._indices = coordinates_store

    @property
    def time_index(self) -> ModelCoordinates:
        """Return the time coordinates."""
        return self._indices.time

    @property
    def scenario_index(self) -> ModelCoordinates:
        """Return the scenario coordinates."""
        return self._indices.scenarios

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

        number_of_timesteps = len(self._indices.time.values)
        all_fixed_load_profiles = []
        for scenario in self._scenarios:
            if scenario.fixed_load_profiles is None:
                profile = [0.0] * number_of_timesteps
            else:
                profile = [0.0] * number_of_timesteps
                for load_profile in scenario.fixed_load_profiles.values():
                    for t in range(number_of_timesteps):
                        profile[t] += load_profile[t]
            all_fixed_load_profiles.append(profile)

        return xr.DataArray(
            data=all_fixed_load_profiles,
            coords=self._indices.scenarios.dimension_coordinates_map | self._indices.time.dimension_coordinates_map,
        )

    @cached_property
    def flexible_load_base_profiles(self) -> xr.DataArray | None:
        """Return flexible load base profiles across scenarios and time."""
        if self._indices.flexible_loads is None:
            return None

        has_any_flexible_loads = any(scenario.flexible_load_base_profiles is not None for scenario in self._scenarios)
        if not has_any_flexible_loads:
            return None

        all_load_profiles = []
        for scenario in self._scenarios:
            scenario_load_profiles_mapping = scenario.flexible_load_base_profiles or {}
            scenario_load_profiles_array = [
                scenario_load_profiles_mapping.get(load_name) for load_name in self._indices.flexible_loads.values
            ]
            all_load_profiles.append(scenario_load_profiles_array)

        return xr.DataArray(
            data=all_load_profiles,
            coords=(
                self._indices.scenarios.dimension_coordinates_map
                | self._indices.flexible_loads.dimension_coordinates_map
                | self._indices.time.dimension_coordinates_map
            ),
        )

    @cached_property
    def market_prices(self) -> xr.DataArray | None:
        """Return market prices across scenarios and time."""
        if self._indices.markets is None:
            return None
        all_market_prices = []
        for scenario in self._scenarios:
            scenario_market_prices_mapping = scenario.market_prices or {}
            scenario_market_prices_array = [
                scenario_market_prices_mapping.get(market_name) for market_name in self._indices.markets.values
            ]
            all_market_prices.append(scenario_market_prices_array)

        return xr.DataArray(
            data=all_market_prices,
            coords=self._indices.scenarios.dimension_coordinates_map
            | self._indices.markets.dimension_coordinates_map
            | self._indices.time.dimension_coordinates_map,
        )

    @cached_property
    def available_capacity_profiles(self) -> xr.DataArray | None:
        """Return available capacity profiles for generators across scenarios and time."""
        if self._indices.generators is None:
            return None
        number_of_timesteps = len(self._indices.time.values)
        all_capacity_profiles = []

        for scenario in self._scenarios:
            profiles = scenario.available_capacity_profiles or {}
            scenario_complete_capacity_profiles = [
                profiles.get(gen_name, [np.inf] * number_of_timesteps) for gen_name in self._indices.generators.values
            ]
            all_capacity_profiles.append(scenario_complete_capacity_profiles)

        return xr.DataArray(
            data=all_capacity_profiles,
            coords=(
                self._indices.scenarios.dimension_coordinates_map
                | self._indices.generators.dimension_coordinates_map
                | self._indices.time.dimension_coordinates_map
            ),
        )

    @cached_property
    def scenario_probabilities(self) -> xr.DataArray:
        """Returns scenario probabilities as xarray DataArray."""
        return xr.DataArray(
            data=[scenario.probability for scenario in self._scenarios],
            coords=self._indices.scenarios.dimension_coordinates_map,
        )
