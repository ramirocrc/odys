"""Unit tests for the charger arrays."""

import pytest

from odys.domain.entities.charger import Charger
from odys.domain.exceptions import OdysError
from odys.parameters.coordinates import Coordinates
from odys.parameters.dimensions import ModelDimension
from odys.parameters.entity_arrays import ChargerArrays
from odys.parameters.vectorize import vectorize

CHARGER1_MAX_POWER = 50.0
CHARGER2_MAX_POWER = 150.0
NUM_CHARGERS = 2


@pytest.fixture
def charger1() -> Charger:
    return Charger(name="charger1", max_power=CHARGER1_MAX_POWER)


@pytest.fixture
def charger2() -> Charger:
    return Charger(name="charger2", max_power=CHARGER2_MAX_POWER)


@pytest.fixture
def charger_arrays(charger1: Charger, charger2: Charger) -> ChargerArrays:
    chargers = [charger1, charger2]
    return vectorize(ChargerArrays, chargers, Coordinates.of_entities(ModelDimension.Chargers, chargers))


def test_charger_arrays_empty_raises_error() -> None:
    """Vectorizing no chargers is an internal error: the charger block is absent instead."""
    with pytest.raises(OdysError, match="ChargerArrays requires at least one model"):
        vectorize(ChargerArrays, [], Coordinates(dimension=ModelDimension.Chargers, labels=()))


def test_charger_arrays_max_power(charger_arrays: ChargerArrays) -> None:
    """Test that max_power property returns correct values."""
    max_power = charger_arrays.max_power
    assert max_power.dims == (ModelDimension.Chargers.value,)
    assert max_power.sel(charger="charger1").values == CHARGER1_MAX_POWER
    assert max_power.sel(charger="charger2").values == CHARGER2_MAX_POWER
