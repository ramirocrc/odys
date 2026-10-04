from types import MappingProxyType
from typing import Any

import pytest
from pydantic import ValidationError

from odys.domain.entities.battery import Battery
from odys.domain.exceptions import OdysValidationError


@pytest.fixture
def battery_base_params() -> MappingProxyType[str, Any]:
    return MappingProxyType({
        "capacity": 100.0,
        "max_charge_power": 50.0,
        "max_discharge_power": 50.0,
        "efficiency_charging": 0.9,
        "efficiency_discharging": 0.85,
        "soc_start": 0.5,
    })


@pytest.mark.parametrize(
    ("param_name", "invalid_value", "expected_match"),
    [
        ("capacity", 0.0, "Input should be greater than 0"),
        ("max_charge_power", 0.0, "Input should be greater than 0"),
        ("max_discharge_power", -0.1, "Input should be greater than or equal to 0"),
        ("efficiency_charging", 0.0, "Input should be greater than 0"),
        ("efficiency_charging", 1.1, "Input should be less than or equal to 1"),
        ("efficiency_discharging", 0.0, "Input should be greater than 0"),
        ("efficiency_discharging", 1.1, "Input should be less than or equal to 1"),
        ("soc_start", -0.1, "Input should be greater than or equal to 0"),
        ("soc_start", 1.1, "Input should be less than or equal to 1"),
        ("soc_end", -0.1, "Input should be greater than or equal to 0"),
        ("soc_end", 1.1, "Input should be less than or equal to 1"),
        ("soc_min", -0.1, "Input should be greater than or equal to 0"),
        ("soc_min", 1.1, "Input should be less than or equal to 1"),
        ("soc_max", 1.1, "Input should be less than or equal to 1"),
        ("degradation_cost", -0.1, "Input should be greater than or equal to 0"),
        ("self_discharge_rate", -0.1, "Input should be greater than or equal to 0"),
        ("self_discharge_rate", 1.1, "Input should be less than or equal to 1"),
    ],
)
def test_battery_creation_with_invalid_parameters_raises_error(
    param_name: str,
    invalid_value: float,
    expected_match: str,
    battery_base_params: MappingProxyType[str, Any],
) -> None:
    base_params = dict(battery_base_params)
    base_params[param_name] = invalid_value
    with pytest.raises(ValidationError, match=expected_match):
        Battery(**base_params)


@pytest.mark.parametrize(
    ("invalid_parameters", "expected_match"),
    [
        ({"soc_start": 0.2, "soc_min": 0.3}, "soc_start \\(0\\.2\\) must be ≥ soc_min \\(0\\.3\\)"),
        ({"soc_start": 0.8, "soc_max": 0.7}, "soc_start \\(0\\.8\\) must be ≤ soc_max \\(0\\.7\\)"),
        ({"soc_end": 0.15, "soc_min": 0.25}, "soc_end \\(0\\.15\\) must be ≥ soc_min \\(0\\.25\\)"),
        ({"soc_end": 0.85, "soc_max": 0.75}, "soc_end \\(0\\.85\\) must be ≤ soc_max \\(0\\.75\\)"),
        ({"soc_min": 0.5, "soc_max": 0.5}, "soc_min \\(0\\.5\\) must be < soc_max \\(0\\.5\\)"),
    ],
)
def test_soc_values_outside_bounds_raises_error(
    invalid_parameters: dict[str, Any],
    expected_match: str,
    battery_base_params: MappingProxyType[str, Any],
) -> None:
    invalid_battery_params = dict(battery_base_params) | invalid_parameters

    with pytest.raises(OdysValidationError, match=expected_match):
        Battery(**invalid_battery_params)


def test_degradation_cost_defaults_to_zero(battery_base_params: MappingProxyType[str, Any]) -> None:
    battery = Battery(**dict(battery_base_params))

    assert battery.degradation_cost == 0.0


def test_battery_is_frozen(battery_base_params: MappingProxyType[str, Any]) -> None:
    battery = Battery(**dict(battery_base_params))
    frozen_field = "capacity"
    with pytest.raises(ValidationError, match="Instance is frozen"):
        setattr(battery, frozen_field, 1.0)


def test_battery_has_no_name(battery_base_params: MappingProxyType[str, Any]) -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Battery.model_validate({**battery_base_params, "name": "bess"})
