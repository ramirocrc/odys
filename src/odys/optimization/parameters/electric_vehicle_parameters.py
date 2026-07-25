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

        ev_names = self._index.values

        if len(ev_names) == 0:
            empty_data = np.empty((0, number_of_timesteps))
            self._is_driving = xr.DataArray(
                empty_data,
                dims=[ModelDimension.EVs.value, ModelDimension.Time.value],
                coords={
                    ModelDimension.EVs.value: [],
                    ModelDimension.Time.value: list(range(number_of_timesteps)),
                },
            )
            self._trip_energy = xr.DataArray(
                empty_data,
                dims=[ModelDimension.EVs.value, ModelDimension.Time.value],
                coords={
                    ModelDimension.EVs.value: [],
                    ModelDimension.Time.value: list(range(number_of_timesteps)),
                },
            )
            self._min_soc_at_departure = xr.DataArray(
                empty_data,
                dims=[ModelDimension.EVs.value, ModelDimension.Time.value],
                coords={
                    ModelDimension.EVs.value: [],
                    ModelDimension.Time.value: list(range(number_of_timesteps)),
                },
            )
            return

        is_driving_data = {}
        for ev in self._evs:
            driving = [0] * number_of_timesteps
            for trip in ev.trips:
                for t in range(trip.start_time, trip.end_time):
                    driving[t] = 1
            is_driving_data[ev.name] = driving

        self._is_driving = xr.DataArray(
            [is_driving_data[name] for name in ev_names],
            dims=[ModelDimension.EVs.value, ModelDimension.Time.value],
            coords={
                ModelDimension.EVs.value: list(ev_names),
                ModelDimension.Time.value: list(range(number_of_timesteps)),
            },
        )

        # trip_energy[ev, time]: energy consumed during trips
        trip_energy_data = {}
        for ev in self._evs:
            energy = [0.0] * number_of_timesteps
            for trip in ev.trips:
                duration = trip.end_time - trip.start_time
                energy_per_step = trip.energy_consumption / duration
                for t in range(trip.start_time, trip.end_time):
                    energy[t] = energy_per_step
            trip_energy_data[ev.name] = energy

        self._trip_energy = xr.DataArray(
            [trip_energy_data[name] for name in ev_names],
            dims=[ModelDimension.EVs.value, ModelDimension.Time.value],
            coords={
                ModelDimension.EVs.value: list(ev_names),
                ModelDimension.Time.value: list(range(number_of_timesteps)),
            },
        )

        # min_soc_at_departure[ev, time]: min SOC required at departure
        min_soc_data = {}
        for ev in self._evs:
            min_soc = [0.0] * number_of_timesteps
            for trip in ev.trips:
                min_soc[trip.start_time] = trip.min_soc_at_departure
            min_soc_data[ev.name] = min_soc

        self._min_soc_at_departure = xr.DataArray(
            [min_soc_data[name] for name in ev_names],
            dims=[ModelDimension.EVs.value, ModelDimension.Time.value],
            coords={
                ModelDimension.EVs.value: list(ev_names),
                ModelDimension.Time.value: list(range(number_of_timesteps)),
            },
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
    def is_driving(self) -> xr.DataArray | None:
        """Return binary array indicating if each EV is driving at each time."""
        return self._is_driving

    @property
    def trip_energy(self) -> xr.DataArray | None:
        """Return energy consumed by each EV at each time during trips."""
        return self._trip_energy

    @property
    def min_soc_at_departure(self) -> xr.DataArray | None:
        """Return min SoC required at departure for each EV at each time."""
        return self._min_soc_at_departure
