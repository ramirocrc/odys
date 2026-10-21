"""Typed parameter arrays of each entity type, vectorized along the entity's dimension.

Each class lists the entity fields the optimization model reads, named exactly
like the domain fields, and is built by `vectorize`. Derived arrays that are not
entity fields (such as EV trip arrays over time, durations in steps, or the
run's initial and final conditions) are built by hand.
"""

from collections.abc import Sequence
from datetime import timedelta
from typing import TypeVar

import numpy as np
import xarray as xr

from odys.domain.conditions import (
    ElectricVehicleFinalState,
    ElectricVehicleInitialState,
    GeneratorFinalState,
    GeneratorInitialState,
    StorageFinalState,
    StorageInitialState,
)
from odys.domain.entities.battery_storage import BatteryStorage
from odys.domain.entities.commitment import Commitment
from odys.domain.entities.electric_vehicle import ElectricVehicle
from odys.domain.entities.generator import Generator
from odys.domain.horizon import Horizon
from odys.parameters.context import ModelContext
from odys.parameters.coordinates import Coordinates
from odys.parameters.vectorize import EntityArrays, vectorize


class GeneratorArrays(EntityArrays):
    """Generator parameters along the generator dimension."""

    nominal_power: xr.DataArray
    variable_cost: xr.DataArray
    min_power: xr.DataArray
    ramp_up: xr.DataArray
    ramp_down: xr.DataArray


class CommitmentArrays(EntityArrays):
    """Commitment parameters along an entity dimension: the cost of each start and stop."""

    startup_cost: xr.DataArray
    shutdown_cost: xr.DataArray


class CommitmentStateArrays(EntityArrays):
    """On/off quantities that depend on the run: minimum times in steps and the initial status.

    Without a minimum time, the minimum is one step. Without a time in state, the
    entity has been in its initial status for longer than any minimum time (`inf`
    steps), so nothing carries over.
    """

    min_up_steps: xr.DataArray
    min_down_steps: xr.DataArray
    initially_on: xr.DataArray
    initial_steps_in_state: xr.DataArray


class GeneratorStateArrays(EntityArrays):
    """Generator quantities that depend on the run: the initial and final power, and the on/off states.

    Without an initial state, the generator starts off (power 0). `final_power` is
    NaN where there is no final state.
    """

    initial_power: xr.DataArray
    final_power: xr.DataArray
    commitment: CommitmentStateArrays


class BatteryArrays(EntityArrays):
    """Battery parameters of battery storages or electric vehicles, along their dimension."""

    capacity: xr.DataArray
    max_charge_power: xr.DataArray
    max_discharge_power: xr.DataArray
    efficiency_charging: xr.DataArray
    efficiency_discharging: xr.DataArray
    self_discharge_rate: xr.DataArray
    soc_min: xr.DataArray
    soc_max: xr.DataArray
    degradation_cost: xr.DataArray


class BatteryStateArrays(EntityArrays):
    """State of charge of each battery at the start of the run and, where set, at its end."""

    soc_start: xr.DataArray
    soc_end: xr.DataArray


class FlexibleLoadArrays(EntityArrays):
    """Flexible load parameters along the flexible load dimension."""

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
    states: BatteryStateArrays
    trips: ElectricVehicleTripArrays


def commitment_state_arrays(
    commitments: Sequence[Commitment],
    coordinates: Coordinates,
    horizon: Horizon,
    initially_on: xr.DataArray,
    initial_steps_in_state: xr.DataArray,
) -> CommitmentStateArrays:
    """Build the minimum up and down times in steps of the given commitments, with their entities' initial status.

    Args:
        commitments: The commitments, in coordinate order.
        coordinates: The labels of their entities along the entity dimension.
        horizon: The time grid of the optimization.
        initially_on: Whether each entity is on just before the first timestep.
        initial_steps_in_state: How many steps each entity has been in its initial status (`inf` when unknown).

    Returns:
        The on/off state arrays.

    """

    def steps(duration: timedelta | None) -> int:
        return 1 if duration is None else horizon.steps_in(duration)

    def along_entities(values: Sequence[float]) -> xr.DataArray:
        return xr.DataArray(values, dims=coordinates.dimension, coords=coordinates.dimension_coordinates_map)

    return CommitmentStateArrays(
        min_up_steps=along_entities([steps(commitment.min_up_time) for commitment in commitments]),
        min_down_steps=along_entities([steps(commitment.min_down_time) for commitment in commitments]),
        initially_on=initially_on,
        initial_steps_in_state=initial_steps_in_state,
    )


def _steps_in_state(time_in_state: timedelta | None, horizon: Horizon) -> float:
    return np.inf if time_in_state is None else horizon.steps_in(time_in_state)


def generator_state_arrays(
    generators: Sequence[Generator],
    coordinates: Coordinates,
    context: ModelContext,
) -> GeneratorStateArrays:
    """Build the generators' initial and final power and their on/off states.

    Args:
        generators: The generators, in coordinate order.
        coordinates: The labels of the generators along the generator dimension.
        context: The shared indexing of the problem, with its horizon and conditions.

    Returns:
        The generators' state arrays.

    """
    initial_power = context.conditions(
        GeneratorInitialState,
        generators,
        coordinates,
        lambda state: state.power,
        default=0.0,
    )
    initial_steps_in_state = context.conditions(
        GeneratorInitialState,
        generators,
        coordinates,
        lambda state: _steps_in_state(state.time_in_state, context.horizon),
        default=np.inf,
    )
    return GeneratorStateArrays(
        initial_power=initial_power,
        final_power=context.conditions(
            GeneratorFinalState,
            generators,
            coordinates,
            lambda state: state.power,
            default=np.nan,
        ),
        commitment=commitment_state_arrays(
            [generator.commitment for generator in generators],
            coordinates,
            context.horizon,
            initially_on=initial_power > 0,
            initial_steps_in_state=initial_steps_in_state,
        ),
    )


def battery_storage_state_arrays(
    storages: Sequence[BatteryStorage],
    coordinates: Coordinates,
    context: ModelContext,
) -> BatteryStateArrays:
    """Build the initial and final state of charge of the battery storages.

    Args:
        storages: The battery storages, in coordinate order.
        coordinates: The labels of the storages along their dimension.
        context: The shared indexing of the problem, with its conditions.

    Returns:
        The storages' state of charge arrays; `soc_end` is NaN where there is no final state.

    """
    return _battery_state_arrays(StorageInitialState, StorageFinalState, storages, coordinates, context)


InitialSocT = TypeVar("InitialSocT", StorageInitialState, ElectricVehicleInitialState)
FinalSocT = TypeVar("FinalSocT", StorageFinalState, ElectricVehicleFinalState)


def _battery_state_arrays(
    initial_kind: type[InitialSocT],
    final_kind: type[FinalSocT],
    assets: Sequence[BatteryStorage] | Sequence[ElectricVehicle],
    coordinates: Coordinates,
    context: ModelContext,
) -> BatteryStateArrays:
    return BatteryStateArrays(
        soc_start=context.conditions(initial_kind, assets, coordinates, lambda state: state.soc),
        soc_end=context.conditions(final_kind, assets, coordinates, lambda state: state.soc, default=np.nan),
    )


def electric_vehicle_arrays(
    electric_vehicles: Sequence[ElectricVehicle],
    coordinates: Coordinates,
    context: ModelContext,
) -> ElectricVehicleArrays:
    """Build the battery, state of charge and trip arrays of the electric vehicles.

    Args:
        electric_vehicles: The electric vehicles, in coordinate order.
        coordinates: The labels of the electric vehicles along the EV dimension.
        context: The shared indexing of the problem, with its time coordinates and conditions.

    Returns:
        The electric vehicles' arrays.

    """
    return ElectricVehicleArrays(
        battery=vectorize(BatteryArrays, [ev.battery for ev in electric_vehicles], coordinates),
        states=_battery_state_arrays(
            ElectricVehicleInitialState,
            ElectricVehicleFinalState,
            electric_vehicles,
            coordinates,
            context,
        ),
        trips=_trip_arrays(electric_vehicles, coordinates, context),
    )


def _trip_arrays(
    electric_vehicles: Sequence[ElectricVehicle],
    coordinates: Coordinates,
    context: ModelContext,
) -> ElectricVehicleTripArrays:
    time = context.time
    steps_in = context.horizon.steps_in
    shape = (len(electric_vehicles), len(time.labels))
    is_driving = np.zeros(shape)
    trip_energy = np.zeros(shape)
    min_soc_at_departure = np.zeros(shape)

    for i, ev in enumerate(electric_vehicles):
        for trip in ev.trips:
            start_step, end_step = steps_in(trip.start_time), steps_in(trip.end_time)
            is_driving[i, start_step:end_step] = 1
            trip_energy[i, start_step:end_step] = trip.energy_consumption / (end_step - start_step)
            min_soc_at_departure[i, start_step] = trip.min_soc_at_departure

    dims = (coordinates.dimension, time.dimension)
    coords = coordinates.dimension_coordinates_map | time.dimension_coordinates_map
    return ElectricVehicleTripArrays(
        is_driving=xr.DataArray(is_driving, dims=dims, coords=coords),
        trip_energy=xr.DataArray(trip_energy, dims=dims, coords=coords),
        min_soc_at_departure=xr.DataArray(min_soc_at_departure, dims=dims, coords=coords),
    )
