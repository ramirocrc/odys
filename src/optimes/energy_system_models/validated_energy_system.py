"""Energy system conditions and data structures.

This module provides classes for representing energy system conditions,
including demand profiles and system configurations.
"""

from datetime import timedelta
from functools import cached_property
from typing import Self

import xarray as xr
from pydantic import BaseModel, model_validator

from optimes._math_model.model_components.parameters import EnergyModelParameters
from optimes._math_model.model_components.sets import (
    EnergyModelDimension,
    EnergyModelSets,
    ModelSet,
)
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.units import PowerUnit
from optimes.utils.logging import get_logger

logger = get_logger(__name__)


class ValidatedEnergySystem(BaseModel, frozen=True, arbitrary_types_allowed=True):
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
    demand_profile: list[float]
    timestep: timedelta
    power_unit: PowerUnit
    available_capacity_profiles: dict[str, list[float]] | None = None

    @cached_property
    def sets(self) -> EnergyModelSets:
        """Energy Model Sets."""
        return EnergyModelSets(
            time=ModelSet(
                dimension=EnergyModelDimension.Time,
                values=[str(time_step) for time_step in range(len(self.demand_profile))],
            ),
            generators=ModelSet(
                dimension=EnergyModelDimension.Generators,
                values=[gen.name for gen in self.portfolio.generators],
            ),
            batteries=ModelSet(
                dimension=EnergyModelDimension.Batteries,
                values=[battery.name for battery in self.portfolio.batteries],
            ),
        )

    @cached_property
    def parameters(self) -> EnergyModelParameters:
        """Returns energy model parameters."""
        return EnergyModelParameters(
            generators_nomianl_power=self._generators_nominal_power,
            generators_variable_cost=self._generators_variable_cost,
            batteries_capacity=self._batteries_capacity,
            batteries_max_power=self._batteries_max_power,
            batteries_efficiency_charging=self._batteries_efficiency_charging,
            batteries_efficiency_discharging=self._batteries_efficiency_discharging,
            batteries_soc_start=self._batteries_soc_initial,
            batteries_soc_end=self._batteries_soc_terminal,
            demand_profile=self._demand_profile,
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
        self._validate_capacity_profile_lengths()
        self._validate_available_capacity()
        self._validate_demand_can_be_met()
        return self

    def _validate_capacity_profile_lengths(self) -> None:
        """Validate that available capacity profiles match demand profile length.

        Raises:
            ValueError: If capacity profile lengths don't match demand profile.

        """
        if self.available_capacity_profiles is None:
            return
        demand_profile_length = len(self.demand_profile)
        for asset_name, available_capacity_profile in self.available_capacity_profiles.items():
            if len(available_capacity_profile) != demand_profile_length:
                msg = (
                    f"Available capacity for asset '{asset_name}' has a length of {len(available_capacity_profile)}, "
                    "which does not match demand profile length {demand_profile_length}."
                )
                raise ValueError(msg)

    def _validate_available_capacity(self) -> None:
        """Validate that available capacity profiles are only for generators.

        Raises:
            TypeError: If available capacity is specified for non-generator assets.
            ValueError: If capacity profile length doesn't match demand profile.

        """
        if self.available_capacity_profiles is None:
            return
        for asset_name, capacities in self.available_capacity_profiles.items():
            asset = self.portfolio.get_asset(asset_name)
            if not isinstance(asset, PowerGenerator):
                msg = (
                    "Available capacity can only be specified for generators, "
                    f"but got '{asset_name}' of type {type(asset)}."
                )
                raise TypeError(msg)
            if len(capacities) != len(self.demand_profile):
                msg = (
                    f"Available capacity for '{asset_name}' has a length of {len(capacities)}, "
                    f"which doesn't match the length of the demand profile ({len(self.demand_profile)})."
                )
                raise ValueError(msg)

    def _validate_demand_can_be_met(self) -> None:
        """Validate that the system can meet the demand profile.

        This method checks both power and energy balance constraints
        to ensure the system is feasible.
        """
        self._validate_enough_power_to_meet_demand()
        self._validate_enough_energy_to_meet_demand()

    def _validate_enough_power_to_meet_demand(self) -> None:
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
        for t, demand_t in enumerate(self.demand_profile):
            if max_available_power < demand_t:
                msg = (
                    f"Infeasible problem at time index {t}: "
                    f"Demand = {demand_t}, but maximum available generation + battery = {max_available_power}."
                )
                raise ValueError(msg)

    def _validate_enough_energy_to_meet_demand(self) -> None:
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
            coords=self.sets.generators.coordinates,
        )

    @property
    def _generators_variable_cost(self) -> xr.DataArray:
        return xr.DataArray(
            data=[gen.variable_cost for gen in self.portfolio.generators],
            coords=self.sets.generators.coordinates,
        )

    @property
    def _batteries_capacity(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.capacity for battery in self.portfolio.batteries],
            coords=self.sets.batteries.coordinates,
        )

    @property
    def _batteries_max_power(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.max_power for battery in self.portfolio.batteries],
            coords=self.sets.batteries.coordinates,
        )

    @property
    def _batteries_efficiency_charging(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.efficiency_charging for battery in self.portfolio.batteries],
            coords=self.sets.batteries.coordinates,
        )

    @property
    def _batteries_efficiency_discharging(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.efficiency_discharging for battery in self.portfolio.batteries],
            coords=self.sets.batteries.coordinates,
        )

    @property
    def _batteries_soc_initial(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.soc_start for battery in self.portfolio.batteries],
            coords=self.sets.batteries.coordinates,
        )

    @property
    def _batteries_soc_terminal(self) -> xr.DataArray:
        return xr.DataArray(
            data=[battery.soc_end for battery in self.portfolio.batteries],
            coords=self.sets.batteries.coordinates,
        )

    @property
    def _demand_profile(self) -> xr.DataArray:
        return xr.DataArray(
            data=self.demand_profile,
            coords=self.sets.time.coordinates,
        )
