import pytest

from odys.domain.entities.standalone_storage import StandaloneStorage
from odys.optimization.parameters.entity_parameters.standalone_storage_parameters import StandaloneStorageParameters

STANDARD_CAPACITY = 100.0
STANDARD_MAX_CHARGE_POWER = 50.0
STANDARD_MAX_DISCHARGE_POWER = 50.0
STANDARD_SOC_START = 0.5
EXPLICIT_DEGRADATION_COST = 5.0


@pytest.fixture
def storage_with_degradation_cost() -> StandaloneStorage:
    return StandaloneStorage(
        name="storage_with_degradation_cost",
        capacity=STANDARD_CAPACITY,
        max_charge_power=STANDARD_MAX_CHARGE_POWER,
        max_discharge_power=STANDARD_MAX_DISCHARGE_POWER,
        soc_start=STANDARD_SOC_START,
        degradation_cost=EXPLICIT_DEGRADATION_COST,
    )


@pytest.fixture
def storage_without_degradation_cost() -> StandaloneStorage:
    return StandaloneStorage(
        name="storage_without_degradation_cost",
        capacity=STANDARD_CAPACITY,
        max_charge_power=STANDARD_MAX_CHARGE_POWER,
        max_discharge_power=STANDARD_MAX_DISCHARGE_POWER,
        soc_start=STANDARD_SOC_START,
    )


def test_degradation_cost_reflects_explicit_value(storage_with_degradation_cost: StandaloneStorage) -> None:
    params = StandaloneStorageParameters([storage_with_degradation_cost])

    value = params.degradation_cost.sel(standalone_storage="storage_with_degradation_cost").item()

    assert value == EXPLICIT_DEGRADATION_COST


def test_degradation_cost_defaults_to_zero_when_not_set(storage_without_degradation_cost: StandaloneStorage) -> None:
    params = StandaloneStorageParameters([storage_without_degradation_cost])

    value = params.degradation_cost.sel(standalone_storage="storage_without_degradation_cost").item()

    assert value == 0.0
