"""Electric vehicle parameters for the mathematical optimization model."""

from collections.abc import Sequence
from typing import ClassVar

import numpy as np
import xarray as xr

from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.optimization.model.sets import ModelDimension, ModelIndex


class ElectricVehicleIndex(ModelIndex):
    """Index for electric vehicle components in the optimization model."""

    dimension: ClassVar[ModelDimension] = ModelDimension.EVs


class ElectricVehicleParameters:
    """Parameters for electric vehicle assets in the energy system model.

    Indexed by EV dimension (only ElectricVehicle instances) to maintain
    semantic correctness and avoid storing zeros for non-EV storages.
    """

    def __init__(
        self,
        number_of_timesteps: int,
        electric_vehicles: Sequence[ElectricVehicle] | None = None,
    ) -> None:
        """Initialize electric vehicle parameters.

        Args:
            number_of_timesteps: Number of timestpes.
            electric_vehicles: Sequence of electric vehicle objects.
        """
        self._evs = list(electric_vehicles) if electric_vehicles else []
        self._index = ElectricVehicleIndex(
            values=tuple(ev.name for ev in self._evs),
        )

        ev_dim = ModelDimension.EVs.value

        battery_data = {
            "capacity": [ev.capacity for ev in self._evs],
            "max_charge_power": [ev.max_charge_power for ev in self._evs],
            "max_discharge_power": [ev.max_discharge_power for ev in self._evs],
            "efficiency_charging": [ev.efficiency_charging for ev in self._evs],
            "efficiency_discharging": [ev.efficiency_discharging for ev in self._evs],
            "self_discharge_rate": [ev.self_discharge_rate for ev in self._evs],
            "soc_start": [ev.soc_start for ev in self._evs],
            "soc_end": [ev.soc_end for ev in self._evs],
            "soc_min": [ev.soc_min for ev in self._evs],
            "soc_max": [ev.soc_max for ev in self._evs],
            "degradation_cost": [ev.degradation_cost for ev in self._evs],
        }
        self._dataset = xr.Dataset(
            {name: (ev_dim, values) for name, values in battery_data.items()},
            coords=self._index.coordinates,
        )

        ev_names = self._index.values
        n_evs = len(ev_names)
        is_driving_data = np.zeros((n_evs, number_of_timesteps))
        trip_energy_data = np.zeros((n_evs, number_of_timesteps))
        min_soc_data = np.zeros((n_evs, number_of_timesteps))

        for i, ev in enumerate(self._evs):
            for trip in ev.trips:
                duration = trip.end_time - trip.start_time
                energy_per_step = trip.energy_consumption / duration
                for t in range(trip.start_time, trip.end_time):
                    is_driving_data[i, t] = 1
                    trip_energy_data[i, t] = energy_per_step
                min_soc_data[i, trip.start_time] = trip.min_soc_at_departure

        time_dim = ModelDimension.Time.value
        time_coords = list(range(number_of_timesteps))
        trip_coords = {ev_dim: list(ev_names), time_dim: time_coords}
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
    def is_empty(self) -> bool:
        """Return True if there are no electric vehicles."""
        return len(self._evs) == 0

    @property
    def index(self) -> ElectricVehicleIndex:
        """Return the electric vehicle index."""
        return self._index

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
