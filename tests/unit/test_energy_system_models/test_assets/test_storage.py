from types import MappingProxyType

import pytest

from odys.energy_system_models.assets.storage import Battery


@pytest.fixture
def battery_base_params() -> MappingProxyType:
    return MappingProxyType({
        "name": "test_battery",
        "capacity": 100.0,
        "max_power": 50.0,
        "efficiency_charging": 0.9,
        "efficiency_discharging": 0.85,
        "soc_start": 0.5,
    })


@pytest.mark.parametrize(
    ("param_name", "invalid_value", "expected_match"),
    [
        ("capacity", 0.0, "Input should be greater than 0"),
        ("max_power", 0.0, "Input should be greater than 0"),
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
    battery_base_params: dict,
) -> None:
    base_params = dict(battery_base_params)
    base_params[param_name] = invalid_value
    with pytest.raises(ValueError, match=expected_match):
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
    invalid_parameters: dict,
    expected_match: str,
    battery_base_params: dict,
) -> None:
    base_params = dict(battery_base_params)
    invalid_battery_params = base_params | invalid_parameters  # The latter takes priority when same key exists

    with pytest.raises(ValueError, match=expected_match):
        Battery(**invalid_battery_params)
