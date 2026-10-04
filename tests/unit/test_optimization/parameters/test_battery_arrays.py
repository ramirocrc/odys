"""Unit tests for the battery arrays of stationary storages."""

import pytest

from odys.domain.entities.battery import Battery
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.parameters.coordinates import Coordinates
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import BatteryArrays
from odys.parameters.vectorize import vectorize

STANDARD_CAPACITY = 100.0
STANDARD_MAX_CHARGE_POWER = 50.0
STANDARD_MAX_DISCHARGE_POWER = 50.0
STANDARD_SOC_START = 0.5
EXPLICIT_DEGRADATION_COST = 5.0
EXPLICIT_SOC_END = 0.4


def _battery_arrays(storages: list[StationaryStorage]) -> BatteryArrays:
    coordinates = Coordinates.of_entities(ModelDimension.StationaryStorages, storages)
    return vectorize(BatteryArrays, [storage.battery for storage in storages], coordinates)


@pytest.fixture
def storage_with_degradation_cost() -> StationaryStorage:
    return StationaryStorage(
        name="storage_with_degradation_cost",
        battery=Battery(
            capacity=STANDARD_CAPACITY,
            max_charge_power=STANDARD_MAX_CHARGE_POWER,
            max_discharge_power=STANDARD_MAX_DISCHARGE_POWER,
            soc_start=STANDARD_SOC_START,
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
            soc_start=STANDARD_SOC_START,
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


def test_unset_soc_end_becomes_nan_in_a_float_array(
    storage_with_degradation_cost: StationaryStorage,
    storage_without_degradation_cost: StationaryStorage,
) -> None:
    with_soc_end = storage_with_degradation_cost.model_copy(
        update={"battery": storage_with_degradation_cost.battery.model_copy(update={"soc_end": EXPLICIT_SOC_END})},
    )
    params = _battery_arrays([with_soc_end, storage_without_degradation_cost])

    assert params.soc_end.dtype.kind == "f"
    assert params.soc_end.sel(stationary_storage="storage_with_degradation_cost").item() == EXPLICIT_SOC_END
    assert bool(params.soc_end.sel(stationary_storage="storage_without_degradation_cost").isnull())
