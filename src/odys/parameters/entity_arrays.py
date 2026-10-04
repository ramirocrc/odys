"""Typed parameter arrays of each entity type, vectorized along the entity's dimension.

Each class lists the entity fields the optimization model reads, named exactly
like the domain fields, and is built by `vectorize`. Derived arrays that are not
entity fields (such as EV trip arrays over time) are built by hand.
"""

from collections.abc import Sequence

import numpy as np
import xarray as xr

from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.parameters.coordinates import Coordinates
from odys.parameters.dimensions import ModelDimension
from odys.parameters.vectorize import EntityArrays, vectorize


class GeneratorArrays(EntityArrays):
    """Generator parameters along the generator dimension."""

    nominal_power: xr.DataArray
    variable_cost: xr.DataArray
    min_power: xr.DataArray
    min_up_time: xr.DataArray
    min_down_time: xr.DataArray
    startup_cost: xr.DataArray
    shutdown_cost: xr.DataArray
    ramp_up: xr.DataArray
    ramp_down: xr.DataArray


class BatteryArrays(EntityArrays):
    """Battery parameters of stationary storages or electric vehicles, along their dimension."""

    capacity: xr.DataArray
    max_charge_power: xr.DataArray
    max_discharge_power: xr.DataArray
    efficiency_charging: xr.DataArray
    efficiency_discharging: xr.DataArray
    self_discharge_rate: xr.DataArray
    soc_start: xr.DataArray
    soc_end: xr.DataArray
    soc_min: xr.DataArray
    soc_max: xr.DataArray
    degradation_cost: xr.DataArray


class FlexibleLoadArrays(EntityArrays):
    """Flexible load parameters along the flexible load dimension."""

    max_increase: xr.DataArray
    max_decrease: xr.DataArray
    value_of_consumption: xr.DataArray


class MarketArrays(EntityArrays):
    """Energy market parameters along the market dimension."""

    max_trading_volume_per_step: xr.DataArray
    stage_fixed: xr.DataArray
    allowed_trade_direction: xr.DataArray


class ChargerArrays(EntityArrays):
    """Charger parameters along the charger dimension."""

    max_power: xr.DataArray


class ElectricVehicleTripArrays(EntityArrays):
    """Trip schedule of each electric vehicle at each timestep, derived from its trips."""

    is_driving: xr.DataArray
    trip_energy: xr.DataArray
    min_soc_at_departure: xr.DataArray


class ElectricVehicleArrays(EntityArrays):
    """Electric vehicle parameters: battery arrays along the EV dimension, trip arrays over EV and time."""

    battery: BatteryArrays
    trips: ElectricVehicleTripArrays


def electric_vehicle_arrays(
    electric_vehicles: Sequence[ElectricVehicle],
    coordinates: Coordinates,
    time: Coordinates,
) -> ElectricVehicleArrays:
    """Build the battery and trip arrays of the electric vehicles.

    Args:
        electric_vehicles: The electric vehicles, in coordinate order.
        coordinates: The labels of the electric vehicles along the EV dimension.
        time: The time coordinates of the problem.

    Returns:
        The electric vehicles' arrays.

    """
    return ElectricVehicleArrays(
        battery=vectorize(BatteryArrays, [ev.battery for ev in electric_vehicles], coordinates),
        trips=_trip_arrays(electric_vehicles, coordinates, time),
    )


def _trip_arrays(
    electric_vehicles: Sequence[ElectricVehicle],
    coordinates: Coordinates,
    time: Coordinates,
) -> ElectricVehicleTripArrays:
    shape = (len(electric_vehicles), len(time.labels))
    is_driving = np.zeros(shape)
    trip_energy = np.zeros(shape)
    min_soc_at_departure = np.zeros(shape)

    for i, ev in enumerate(electric_vehicles):
        for trip in ev.trips:
            trip_steps = slice(trip.start_time, trip.end_time)
            is_driving[i, trip_steps] = 1
            trip_energy[i, trip_steps] = trip.energy_consumption / (trip.end_time - trip.start_time)
            min_soc_at_departure[i, trip.start_time] = trip.min_soc_at_departure

    dims = (ModelDimension.EVs.value, ModelDimension.Time.value)
    coords = coordinates.dimension_coordinates_map | time.dimension_coordinates_map
    return ElectricVehicleTripArrays(
        is_driving=xr.DataArray(is_driving, dims=dims, coords=coords),
        trip_energy=xr.DataArray(trip_energy, dims=dims, coords=coords),
        min_soc_at_departure=xr.DataArray(min_soc_at_departure, dims=dims, coords=coords),
    )
