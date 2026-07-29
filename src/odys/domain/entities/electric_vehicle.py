"""Electric vehicle asset implementation.

This module provides the ElectricVehicle class for modeling electric vehicles
in energy system optimization problems.
"""

from odys.domain.entities.storage import Storage
from odys.domain.entities.trip import Trip
from odys.domain.exceptions import OdysValidationError


class ElectricVehicle(Storage):
    """Electric vehicle — a storage asset with trip constraints.

    Inherits all battery physics from Storage. Adds trip schedule
    that makes the vehicle unavailable for charging during driving
    and consumes energy.

    V2G capability is implicit: if max_discharge_power > 0, the EV
    can discharge through a V2G-capable charger.
    """

    trips: tuple[Trip, ...]

    def asset_type(self) -> str:
        """Return the type of storage asset."""
        return "electric_vehicle"

    def validate_no_overlapping_trips(self) -> None:
        """Validate that this vehicle's trips do not overlap.

        Raises:
            OdysValidationError: If any trips overlap.
        """
        sorted_trips = sorted(self.trips, key=lambda t: t.start_time)
        for i in range(len(sorted_trips) - 1):
            if sorted_trips[i].end_time > sorted_trips[i + 1].start_time:
                msg = (
                    f"Trips '{sorted_trips[i].name}' and '{sorted_trips[i + 1].name}' overlap for vehicle '{self.name}'"
                )
                raise OdysValidationError(msg)

    def validate_trips_within_horizon(self, number_of_steps: int) -> None:
        """Validate that all trips fall within the optimization horizon.

        Args:
            number_of_steps: Total number of timesteps in the optimization.

        Raises:
            OdysValidationError: If any trip extends beyond the horizon.
        """
        for trip in self.trips:
            if trip.start_time >= number_of_steps or trip.end_time > number_of_steps:
                msg = (
                    f"Trip '{trip.name}' for vehicle '{self.name}' extends beyond "
                    f"optimization horizon (start={trip.start_time}, end={trip.end_time}, "
                    f"horizon={number_of_steps})"
                )
                raise OdysValidationError(msg)

    def validate_min_soc_at_departure_feasible(self) -> None:
        """Validate that min_soc_at_departure is feasible for trips starting at t=0.

        A trip departing at t=0 has no prior timestep to charge, so the required
        min_soc_at_departure must not exceed the initial soc_start.

        Raises:
            OdysValidationError: If any trip at t=0 requires more SoC than soc_start.
        """
        for trip in self.trips:
            if trip.start_time == 0 and trip.min_soc_at_departure > self.soc_start:
                msg = (
                    f"Trip '{trip.name}' for vehicle '{self.name}' departs at t=0 with "
                    f"min_soc_at_departure={trip.min_soc_at_departure} > soc_start={self.soc_start}"
                )
                raise OdysValidationError(msg)
