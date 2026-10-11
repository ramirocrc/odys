"""Unit tests for the battery and state of charge arrays of stationary storages."""

from datetime import timedelta

import pytest

from odys.domain.conditions import ConditionSet, StorageFinalState, StorageInitialState
from odys.domain.entities.battery import Battery
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.domain.exceptions import OdysError
from odys.domain.horizon import Horizon
from odys.domain.scenario import Scenario, ScenarioSet
from odys.parameters.context import ModelContext
from odys.parameters.coordinates import Coordinates
from odys.parameters.entity_arrays import BatteryArrays, stationary_storage_state_arrays
from odys.parameters.vectorize import vectorize

STORAGE_DIMENSION = "stationary_storage"

STANDARD_CAPACITY = 100.0
STANDARD_MAX_CHARGE_POWER = 50.0
STANDARD_MAX_DISCHARGE_POWER = 50.0
STANDARD_SOC_START = 0.5
EXPLICIT_DEGRADATION_COST = 5.0
EXPLICIT_SOC_END = 0.4


def _battery_arrays(storages: list[StationaryStorage]) -> BatteryArrays:
    coordinates = Coordinates.of_entities(STORAGE_DIMENSION, storages)
    return vectorize(BatteryArrays, [storage.battery for storage in storages], coordinates)


@pytest.fixture
def storage_with_degradation_cost() -> StationaryStorage:
    return StationaryStorage(
        name="storage_with_degradation_cost",
        battery=Battery(
            capacity=STANDARD_CAPACITY,
            max_charge_power=STANDARD_MAX_CHARGE_POWER,
            max_discharge_power=STANDARD_MAX_DISCHARGE_POWER,
            degradation_cost=EXPLICIT_DEGRADATION_COST,
        ),
    )


@pytest.fixture
def storage_without_degradation_cost() -> StationaryStorage:
    return StationaryStorage(
        name="storage_without_degradation_cost",
        battery=Battery(
            capacity=STANDARD_CAPACITY,
            max_charge_power=STANDARD_MAX_CHARGE_POWER,
            max_discharge_power=STANDARD_MAX_DISCHARGE_POWER,
        ),
    )


def test_degradation_cost_reflects_explicit_value(storage_with_degradation_cost: StationaryStorage) -> None:
    params = _battery_arrays([storage_with_degradation_cost])

    value = params.degradation_cost.sel(stationary_storage="storage_with_degradation_cost").item()

    assert value == EXPLICIT_DEGRADATION_COST


def test_degradation_cost_defaults_to_zero_when_not_set(storage_without_degradation_cost: StationaryStorage) -> None:
    params = _battery_arrays([storage_without_degradation_cost])

    value = params.degradation_cost.sel(stationary_storage="storage_without_degradation_cost").item()

    assert value == 0.0


def _context(condition_set: ConditionSet) -> ModelContext:
    return ModelContext(
        horizon=Horizon(timestep=timedelta(hours=1), number_of_steps=1),
        scenario_set=ScenarioSet(scenarios=(Scenario(),)),
        condition_set=condition_set,
    )


def test_state_arrays_read_soc_start_and_leave_unset_soc_end_nan(
    storage_with_degradation_cost: StationaryStorage,
    storage_without_degradation_cost: StationaryStorage,
) -> None:
    storages = [storage_with_degradation_cost, storage_without_degradation_cost]
    condition_set = ConditionSet(
        initial=tuple(StorageInitialState(storage=storage, soc=STANDARD_SOC_START) for storage in storages),
        final=(StorageFinalState(storage=storage_with_degradation_cost, soc=EXPLICIT_SOC_END),),
    )

    states = stationary_storage_state_arrays(
        storages,
        Coordinates.of_entities(STORAGE_DIMENSION, storages),
        _context(condition_set),
    )

    assert states.soc_start.values.tolist() == pytest.approx([STANDARD_SOC_START, STANDARD_SOC_START])
    assert states.soc_end.dtype.kind == "f"
    assert states.soc_end.sel(stationary_storage="storage_with_degradation_cost").item() == EXPLICIT_SOC_END
    assert bool(states.soc_end.sel(stationary_storage="storage_without_degradation_cost").isnull())


def test_state_arrays_without_initial_state_raise(storage_without_degradation_cost: StationaryStorage) -> None:
    """Validation requires an initial state for every storage, so a missing one is an internal error."""
    storages = [storage_without_degradation_cost]

    with pytest.raises(OdysError, match="There is no StorageInitialState for 'storage_without_degradation_cost'"):
        stationary_storage_state_arrays(
            storages,
            Coordinates.of_entities(STORAGE_DIMENSION, storages),
            _context(ConditionSet()),
        )
