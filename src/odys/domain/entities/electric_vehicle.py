"""Electric vehicle asset implementation.

This module provides the ElectricVehicle class for modeling electric vehicles
in energy system optimization problems.
"""

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

    Trips must not overlap, which is checked at construction. Whether a trip
    departing at the start fits the starting charge is checked by the vehicle's
    `ElectricVehicleInitialState`.
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

    def max_supply(self, conditions: OperatingConditions) -> tuple[float, ...]:
        """Return the battery's maximum discharge power at each timestep, in MW."""
        return (self.battery.max_discharge_power,) * conditions.horizon.number_of_steps

    def max_energy_supply(self, conditions: OperatingConditions) -> float:
        """Return the energy the battery can discharge over the horizon, in MWh.

        A full battery is emptied at most once, at no more than its maximum discharge power.
        """
        return min(self.battery.capacity, super().max_energy_supply(conditions))

    def validate_horizon(self, horizon: Horizon) -> None:
        """Validate that every trip starts and ends on a timestep and within the optimization horizon.

        Args:
            horizon: The time grid of the optimization.

        Raises:
            OdysValidationError: If a trip time is not a whole number of timesteps, or a trip
                extends beyond the horizon.
        """
        for trip in self.trips:
            for field, time in (("start_time", trip.start_time), ("end_time", trip.end_time)):
                if not horizon.is_whole_steps(time):
                    msg = (
                        f"Trip '{trip.name}' for vehicle '{self.name}' has {field}={time}, "
                        f"which is not a whole number of timesteps ({horizon.timestep})."
                    )
                    raise OdysValidationError(msg)
            if trip.end_time > horizon.timestep * horizon.number_of_steps:
                msg = (
                    f"Trip '{trip.name}' for vehicle '{self.name}' extends beyond "
                    f"optimization horizon (start={trip.start_time}, end={trip.end_time}, "
                    f"horizon={horizon.number_of_steps} steps of {horizon.timestep})"
                )
                raise OdysValidationError(msg)
