"""Unit tests for the Charger entity."""

from types import MappingProxyType
from typing import Any

import pytest
from pydantic import ValidationError

from odys.domain.entities.charger import Charger

CHARGER_MAX_POWER = 50.0
CHARGER_EFFICIENCY = 0.95


@pytest.fixture
def charger_base_params() -> MappingProxyType[str, Any]:
    return MappingProxyType({
        "name": "charger_1",
        "max_power": CHARGER_MAX_POWER,
    })


def test_charger_creation_with_valid_parameters(charger_base_params: MappingProxyType[str, Any]) -> None:
    charger = Charger(**dict(charger_base_params))
    assert charger.name == "charger_1"
    assert charger.max_power == CHARGER_MAX_POWER
    assert charger.efficiency == 1.0


def test_charger_creation_with_efficiency(charger_base_params: MappingProxyType[str, Any]) -> None:
    charger = Charger(**dict(charger_base_params), efficiency=CHARGER_EFFICIENCY)
    assert charger.efficiency == CHARGER_EFFICIENCY


@pytest.mark.parametrize(
    ("param_name", "invalid_value", "expected_match"),
    [
        ("max_power", 0.0, "Input should be greater than 0"),
        ("max_power", -10.0, "Input should be greater than 0"),
        ("efficiency", 0.0, "Input should be greater than 0"),
        ("efficiency", 1.1, "Input should be less than or equal to 1"),
        ("efficiency", -0.1, "Input should be greater than 0"),
    ],
)
def test_charger_creation_with_invalid_parameters_raises_error(
    param_name: str,
    invalid_value: float,
    expected_match: str,
    charger_base_params: MappingProxyType[str, Any],
) -> None:
    base_params = dict(charger_base_params)
    base_params[param_name] = invalid_value
    with pytest.raises(ValidationError, match=expected_match):
        Charger(**base_params)
