from types import MappingProxyType

import pytest

from optimes.energy_system.assets.storage import Battery


@pytest.fixture
def battery_base_params() -> MappingProxyType:
    return MappingProxyType({
        "name": "test_battery",
        "capacity": 100.0,
        "max_power": 50.0,
        "efficiency_charging": 0.9,
        "efficiency_discharging": 0.85,
        "soc_initial": 50.0,
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
        ("soc_initial", -0.1, "Input should be greater than or equal to 0"),
        ("soc_terminal", -0.1, "Input should be greater than or equal to 0"),
        ("soc_min", -0.1, "Input should be greater than or equal to 0"),
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
    ("soc_param", "invalid_value", "expected_match"),
    [
        ("soc_initial", 150.0, "soc_initial \\(150\\.0\\) must be less than the battery capacity \\(100\\.0\\)"),
        ("soc_terminal", 120.0, "soc_terminal \\(120\\.0\\) must be less than the battery capacity \\(100\\.0\\)"),
        ("soc_min", 150.0, "soc_min \\(150\\.0\\) must be less than the battery capacity \\(100\\.0\\)"),
        ("soc_max", 200.0, "soc_max \\(200\\.0\\) must be less than the battery capacity \\(100\\.0\\)"),
    ],
)
def test_soc_values_exceeding_capacity_raises_error(
    soc_param: str,
    invalid_value: float,
    expected_match: str,
    battery_base_params: dict,
) -> None:
    base_params = dict(battery_base_params)
    base_params[soc_param] = invalid_value

    with pytest.raises(ValueError, match=expected_match):
        Battery(**base_params)


@pytest.mark.parametrize(
    ("invalid_parameters", "expected_match"),
    [
        ({"soc_initial": 20.0, "soc_min": 30.0}, "soc_initial \\(20\\.0\\) must be ≥ soc_min \\(30\\.0\\)"),
        ({"soc_initial": 80.0, "soc_max": 70.0}, "soc_initial \\(80\\.0\\) must be ≤ soc_max \\(70\\.0\\)"),
        ({"soc_terminal": 15.0, "soc_min": 25.0}, "soc_terminal \\(15\\.0\\) must be ≥ soc_min \\(25\\.0\\)"),
        ({"soc_terminal": 85.0, "soc_max": 75.0}, "soc_terminal \\(85\\.0\\) must be ≤ soc_max \\(75\\.0\\)"),
        ({"soc_min": 50.0, "soc_max": 50.0}, "soc_min \\(50\\.0\\) must be < soc_max \\(50\\.0\\)"),
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
