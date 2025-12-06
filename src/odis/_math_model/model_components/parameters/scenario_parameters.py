"""Scenario parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar

import numpy as np
import xarray as xr

from odis._math_model.model_components.parameters.battery_parameters import BatteryIndex
from odis._math_model.model_components.parameters.generator_parameters import GeneratorIndex
from odis._math_model.model_components.parameters.load_parameters import LoadIndex
from odis._math_model.model_components.parameters.market_parameters import MarketIndex
from odis._math_model.model_components.sets import ModelDimension, ModelIndex
from odis.energy_system_models.scenarios import StochasticScenario


class TimeIndex(ModelIndex, frozen=True):
    """Index for time components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Time


class ScenarioIndex(ModelIndex, frozen=True):
    """Index for scenario components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.Scenarios


class ScenarioParameters:
    """Parameters for scenarios in the energy system model."""

    def __init__(  # noqa: PLR0913
        self,
        number_of_timesteps: int,
        scenarios: Sequence[StochasticScenario],
        generators_index: GeneratorIndex | None,
        batteries_index: BatteryIndex | None,
        markets_index: MarketIndex | None,
        loads_index: LoadIndex | None,
    ) -> None:
        """Initialize scenario parameters.

        Args:
            number_of_timesteps: Number of time steps in the scenarios.
            scenarios: Sequence of stochastic scenario objects.
            generators_index: Optional generator index.
            batteries_index: Optional battery index.
            markets_index: Optional market index.
            loads_index: Optional load index.
        """
        self._number_of_timesteps = number_of_timesteps
        self._scenarios = scenarios
        self._generators_index = generators_index
        self._batteries_index = batteries_index
        self._markets_index = markets_index
        self._loads_index = loads_index
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

    @property
    def load_profiles(self) -> xr.DataArray | None:
        """Return load profiles across scenarios and time."""
        if self._loads_index is None:
            return None
        all_load_profiles = []
        for scenario in self._scenarios:
            scenario_load_profiles_mapping = scenario.load_profiles or {}
            scenario_load_profiles_array = [
                scenario_load_profiles_mapping.get(load_name) for load_name in self._loads_index.values
            ]
            all_load_profiles.append(scenario_load_profiles_array)

        return xr.DataArray(
            data=all_load_profiles,
            coords=self._scenario_index.coordinates | self._loads_index.coordinates | self._time_index.coordinates,
        )

    @property
    def market_prices(self) -> xr.DataArray | None:
        """Return market prices across scenarios and time."""
        if self._markets_index is None:
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

    @property
    def available_capacity_profiles(self) -> xr.DataArray | None:
        """Return available capacity profiles for generators across scenarios and time."""
        if self._generators_index is None:
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

    @property
    def scenario_probabilities(self) -> xr.DataArray:
        """Returns scenario probabilities as xarray DataArray."""
        return xr.DataArray(
            data=[scenario.probability for scenario in self._scenarios],
            coords=self._scenario_index.coordinates,
        )
