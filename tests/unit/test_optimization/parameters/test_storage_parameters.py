import pytest

from odys.domain.entities.storage import Storage
from odys.optimization.parameters.storage_parameters import StorageParameters

STANDARD_CAPACITY = 100.0
STANDARD_MAX_POWER = 50.0
STANDARD_SOC_START = 0.5
EXPLICIT_DEGRADATION_COST = 5.0


@pytest.fixture
def storage_with_degradation_cost() -> Storage:
    return Storage(
        name="storage_with_degradation_cost",
        capacity=STANDARD_CAPACITY,
        max_power=STANDARD_MAX_POWER,
        soc_start=STANDARD_SOC_START,
        degradation_cost=EXPLICIT_DEGRADATION_COST,
    )


@pytest.fixture
def storage_without_degradation_cost() -> Storage:
    return Storage(
        name="storage_without_degradation_cost",
        capacity=STANDARD_CAPACITY,
        max_power=STANDARD_MAX_POWER,
        soc_start=STANDARD_SOC_START,
    )


def test_degradation_cost_reflects_explicit_value(storage_with_degradation_cost: Storage) -> None:
    params = StorageParameters([storage_with_degradation_cost])

    value = params.degradation_cost.sel(storage="storage_with_degradation_cost").item()

    assert value == EXPLICIT_DEGRADATION_COST


def test_degradation_cost_defaults_to_zero_when_not_set(storage_without_degradation_cost: Storage) -> None:
    params = StorageParameters([storage_without_degradation_cost])

    value = params.degradation_cost.sel(storage="storage_without_degradation_cost").item()

    assert value == 0.0
