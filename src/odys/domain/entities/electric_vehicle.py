"""Electric vehicle asset implementation.

This module provides the ElectricVehicle class for modeling electric vehicles
in energy system optimization problems.
"""

import math
from itertools import pairwise
from typing import Self

from pydantic import model_validator

from odys.domain.entities.base import Asset
from odys.domain.entities.battery import Battery
from odys.domain.entities.trip import Trip
from odys.domain.exceptions import OdysValidationError
from odys.domain.horizon import Horizon, OperatingConditions


class ElectricVehicle(Asset):
    """An electric vehicle.

    The vehicle has a battery and a trip schedule. Trips make the vehicle
    unavailable for charging while driving and consume energy from the battery.

    V2G capability is implicit: if `battery.max_discharge_power > 0`, the EV
    can discharge through a V2G-capable charger.

    Trips must not overlap. A trip departing at t=0 must not require more state
    of charge than `battery.soc_start`, and its energy must fit in the starting
    charge above `soc_min`, since the vehicle cannot charge before or during it.
    These are checked at construction.
    """

    battery: Battery
    trips: tuple[Trip, ...]

    @model_validator(mode="after")
    def _validate_no_overlapping_trips(self) -> Self:
        sorted_trips = sorted(self.trips, key=lambda t: t.start_time)
        for trip, next_trip in pairwise(sorted_trips):
            if trip.end_time > next_trip.start_time:
                msg = f"Trips '{trip.name}' and '{next_trip.name}' overlap for vehicle '{self.name}'"
                raise OdysValidationError(msg)
        return self

    @model_validator(mode="after")
    def _validate_min_soc_at_departure_feasible(self) -> Self:
        for trip in self.trips:
            if trip.start_time == 0 and trip.min_soc_at_departure > self.battery.soc_start:
                msg = (
                    f"Trip '{trip.name}' for vehicle '{self.name}' departs at t=0 with "
                    f"min_soc_at_departure={trip.min_soc_at_departure} > soc_start={self.battery.soc_start}"
                )
                raise OdysValidationError(msg)
        return self

    @model_validator(mode="after")
    def _validate_starting_charge_covers_trip_at_t0(self) -> Self:
        battery = self.battery
        available_energy = (battery.soc_start - battery.soc_min) * battery.capacity
        for trip in self.trips:
            if trip.start_time != 0:
                continue
            if trip.energy_consumption > available_energy and not math.isclose(
                trip.energy_consumption,
                available_energy,
            ):
                msg = (
                    f"Trip '{trip.name}' for vehicle '{self.name}' departs at t=0 and consumes "
                    f"{trip.energy_consumption:.6g} MWh, but the battery holds only {available_energy:.6g} MWh "
                    f"above soc_min at the start (soc_start={battery.soc_start}, soc_min={battery.soc_min}, "
                    f"capacity={battery.capacity} MWh); it cannot charge before or during the trip."
                )
                raise OdysValidationError(msg)
        return self

    def max_supply(self, conditions: OperatingConditions) -> tuple[float, ...]:
        """Return the battery's maximum discharge power at each timestep, in MW."""
        return (self.battery.max_discharge_power,) * conditions.horizon.number_of_steps

    def max_energy_supply(self, conditions: OperatingConditions) -> float:
        """Return the energy the battery can discharge over the horizon, in MWh.

        A full battery is emptied at most once, at no more than its maximum discharge power.
        """
        return min(self.battery.capacity, super().max_energy_supply(conditions))

    def validate_horizon(self, horizon: Horizon) -> None:
        """Validate that all trips fall within the optimization horizon.

        Args:
            horizon: The time grid of the optimization.

        Raises:
            OdysValidationError: If any trip extends beyond the horizon.
        """
        for trip in self.trips:
            if trip.end_time > horizon.number_of_steps:
                msg = (
                    f"Trip '{trip.name}' for vehicle '{self.name}' extends beyond "
                    f"optimization horizon (start={trip.start_time}, end={trip.end_time}, "
                    f"horizon={horizon.number_of_steps})"
                )
                raise OdysValidationError(msg)
