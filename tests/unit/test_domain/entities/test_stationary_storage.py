import pytest
from pydantic import ValidationError

from odys.domain.entities.base import Asset
from odys.domain.entities.battery import Battery
from odys.domain.entities.stationary_storage import StationaryStorage

STORAGE_CAPACITY = 100.0
STORAGE_POWER = 50.0
SOC_START = 0.5


@pytest.fixture
def battery() -> Battery:
    return Battery(
        capacity=STORAGE_CAPACITY,
        max_charge_power=STORAGE_POWER,
        max_discharge_power=STORAGE_POWER,
        soc_start=SOC_START,
    )


def test_stationary_storage_is_an_asset_that_has_a_battery(battery: Battery) -> None:
    storage = StationaryStorage(name="bess", battery=battery)

    assert isinstance(storage, Asset)
    assert storage.battery is battery


def test_stationary_storage_rejects_battery_fields_at_top_level() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        StationaryStorage.model_validate({
            "name": "bess",
            "capacity": STORAGE_CAPACITY,
            "max_charge_power": STORAGE_POWER,
            "max_discharge_power": STORAGE_POWER,
            "soc_start": SOC_START,
        })


def test_stationary_storage_requires_a_battery() -> None:
    with pytest.raises(ValidationError, match="battery"):
        StationaryStorage.model_validate({"name": "bess"})
