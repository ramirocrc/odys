"""Electric vehicle parameters for the mathematical optimization model."""

from collections.abc import Sequence

import numpy as np
import xarray as xr

from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.exceptions import OdysValidationError
from odys.optimization.model.dimensions import ModelDimension


class ElectricVehicleParameters:
    """Parameters for electric vehicle assets in the energy system model.

    Coordinates use the EV dimension (only ElectricVehicle instances) to maintain
    a separate decision-variable space from stationary storage.
    """

    def __init__(
        self,
        number_of_timesteps: int,
        electric_vehicles: Sequence[ElectricVehicle],
    ) -> None:
        """Initialize electric vehicle parameters.

        Args:
            number_of_timesteps: Number of timesteps.
            electric_vehicles: Non-empty sequence of electric vehicle objects.

        Raises:
            OdysValidationError: If electric_vehicles is empty.
        """
        if not electric_vehicles:
            msg = "ElectricVehicleParameters requires at least one electric vehicle."
            raise OdysValidationError(msg)
        ev_names = [ev.name for ev in electric_vehicles]
        ev_dim = ModelDimension.EVs
        time_dim = ModelDimension.Time
        time_coords = [str(t) for t in range(number_of_timesteps)]

        battery_data = {
            "capacity": [ev.capacity for ev in electric_vehicles],
            "max_charge_power": [ev.max_charge_power for ev in electric_vehicles],
            "max_discharge_power": [ev.max_discharge_power for ev in electric_vehicles],
            "efficiency_charging": [ev.efficiency_charging for ev in electric_vehicles],
            "efficiency_discharging": [ev.efficiency_discharging for ev in electric_vehicles],
            "self_discharge_rate": [ev.self_discharge_rate for ev in electric_vehicles],
            "soc_start": [ev.soc_start for ev in electric_vehicles],
            "soc_end": [ev.soc_end for ev in electric_vehicles],
            "soc_min": [ev.soc_min for ev in electric_vehicles],
            "soc_max": [ev.soc_max for ev in electric_vehicles],
            "degradation_cost": [ev.degradation_cost for ev in electric_vehicles],
        }
        self._dataset = xr.Dataset(
            {name: (ev_dim, values) for name, values in battery_data.items()},
            coords={ev_dim: ev_names},
        )

        n_evs = len(ev_names)
        is_driving_data = np.zeros((n_evs, number_of_timesteps))
        trip_energy_data = np.zeros((n_evs, number_of_timesteps))
        min_soc_data = np.zeros((n_evs, number_of_timesteps))

        for i, ev in enumerate(electric_vehicles):
            for trip in ev.trips:
                duration = trip.end_time - trip.start_time
                energy_per_step = trip.energy_consumption / duration
                for t in range(trip.start_time, trip.end_time):
                    is_driving_data[i, t] = 1
                    trip_energy_data[i, t] = energy_per_step
                min_soc_data[i, trip.start_time] = trip.min_soc_at_departure

        trip_coords = {ev_dim: ev_names, time_dim: time_coords}
        self._is_driving = xr.DataArray(
            is_driving_data,
            dims=[ev_dim, time_dim],
            coords=trip_coords,
        )
        self._trip_energy = xr.DataArray(
            trip_energy_data,
            dims=[ev_dim, time_dim],
            coords=trip_coords,
        )
        self._min_soc_at_departure = xr.DataArray(
            min_soc_data,
            dims=[ev_dim, time_dim],
            coords=trip_coords,
        )

    @property
    def is_driving(self) -> xr.DataArray:
        """Return binary array indicating if each EV is driving at each time."""
        return self._is_driving

    @property
    def trip_energy(self) -> xr.DataArray:
        """Return energy consumed by each EV at each time during trips."""
        return self._trip_energy

    @property
    def min_soc_at_departure(self) -> xr.DataArray:
        """Return min SoC required at departure for each EV at each time."""
        return self._min_soc_at_departure

    @property
    def capacity(self) -> xr.DataArray:
        """Return EV battery capacity data."""
        return self._dataset["capacity"]

    @property
    def max_charge_power(self) -> xr.DataArray:
        """Return EV maximum charging power data."""
        return self._dataset["max_charge_power"]

    @property
    def max_discharge_power(self) -> xr.DataArray:
        """Return EV maximum discharging power data."""
        return self._dataset["max_discharge_power"]

    @property
    def efficiency_charging(self) -> xr.DataArray:
        """Return EV charging efficiency data."""
        return self._dataset["efficiency_charging"]

    @property
    def efficiency_discharging(self) -> xr.DataArray:
        """Return EV discharging efficiency data."""
        return self._dataset["efficiency_discharging"]

    @property
    def self_discharge_rate(self) -> xr.DataArray:
        """Return EV self discharge rate data."""
        return self._dataset["self_discharge_rate"]

    @property
    def soc_start(self) -> xr.DataArray:
        """Return EV initial state of charge data."""
        return self._dataset["soc_start"]

    @property
    def soc_end(self) -> xr.DataArray:
        """Return EV final state of charge data."""
        return self._dataset["soc_end"]

    @property
    def soc_min(self) -> xr.DataArray:
        """Return EV minimum state of charge data."""
        return self._dataset["soc_min"]

    @property
    def soc_max(self) -> xr.DataArray:
        """Return EV maximum state of charge data."""
        return self._dataset["soc_max"]

    @property
    def degradation_cost(self) -> xr.DataArray:
        """Return EV degradation cost data."""
        return self._dataset["degradation_cost"]
