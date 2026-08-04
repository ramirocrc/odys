"""Unit tests for ChargerParameters."""

import pytest

from odys.domain.entities.charger import Charger
from odys.optimization.model.sets import ModelDimension
from odys.optimization.parameters.entity_parameters.charger_parameters import ChargerParameters

CHARGER1_MAX_POWER = 50.0
CHARGER1_EFFICIENCY = 0.95
CHARGER2_MAX_POWER = 150.0
CHARGER2_EFFICIENCY = 0.98
NUM_CHARGERS = 2


@pytest.fixture
def charger1() -> Charger:
    return Charger(name="charger1", max_power=CHARGER1_MAX_POWER, efficiency=CHARGER1_EFFICIENCY)


@pytest.fixture
def charger2() -> Charger:
    return Charger(name="charger2", max_power=CHARGER2_MAX_POWER, efficiency=CHARGER2_EFFICIENCY)


@pytest.fixture
def charger_parameters(charger1: Charger, charger2: Charger) -> ChargerParameters:
    return ChargerParameters([charger1, charger2])


def test_charger_parameters_creation(charger_parameters: ChargerParameters) -> None:
    """Test that ChargerParameters can be created with chargers."""
    assert not charger_parameters.is_empty
    assert charger_parameters.index.dimension == ModelDimension.Chargers
    assert len(charger_parameters.index.values) == NUM_CHARGERS


def test_charger_parameters_empty() -> None:
    """Test that empty ChargerParameters can be created."""
    params = ChargerParameters()
    assert params.is_empty
    assert len(params.index.values) == 0


def test_charger_parameters_max_power(charger_parameters: ChargerParameters) -> None:
    """Test that max_power property returns correct values."""
    max_power = charger_parameters.max_power
    assert max_power.dims == (ModelDimension.Chargers.value,)
    assert max_power.sel(charger="charger1").values == CHARGER1_MAX_POWER
    assert max_power.sel(charger="charger2").values == CHARGER2_MAX_POWER


def test_charger_parameters_efficiency(charger_parameters: ChargerParameters) -> None:
    """Test that efficiency property returns correct values."""
    efficiency = charger_parameters.efficiency
    assert efficiency.dims == (ModelDimension.Chargers.value,)
    assert efficiency.sel(charger="charger1").values == CHARGER1_EFFICIENCY
    assert efficiency.sel(charger="charger2").values == CHARGER2_EFFICIENCY


def test_charger_parameters_index(charger_parameters: ChargerParameters) -> None:
    """Test that index property returns correct index."""
    index = charger_parameters.index
    assert index.dimension == ModelDimension.Chargers
    assert index.values == ("charger1", "charger2")
