from datetime import timedelta

import pandas as pd
import pytest

from optimes.energy_system import EnergySystem
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery


@pytest.fixture
def energy_system_sample() -> EnergySystem:
    generator_1 = PowerGenerator(
        name="generator_1",
        nominal_power=100.0,
        variable_cost=20.0,
    )
    generator_2 = PowerGenerator(
        name="generator_2",
        nominal_power=150.0,
        variable_cost=25.0,
    )
    battery_1 = Battery(
        name="battery_1",
        max_power=200.0,
        capacity=100.0,
        efficiency_charging=1,
        efficiency_discharging=1,
        soc_initial=100.0,
        soc_terminal=50.0,
    )
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(battery_1)

    return EnergySystem(
        portfolio=portfolio,
        demand_profile=[50, 75, 100, 125, 150],
        timestep=timedelta(minutes=30),
        power_unit="MW",
    )


def test_solving_and_termination_condition(energy_system_sample: EnergySystem) -> None:
    result = energy_system_sample.optimize()
    assert result.solving_status == "ok"
    assert result.termination_condition == "optimal"


def test_detailed_results_format(energy_system_sample: EnergySystem) -> None:
    result = energy_system_sample.optimize()

    detailed_results = result.to_dataframe("detailed")
    expected_columns = pd.Index(["value"])
    expected_index = pd.MultiIndex.from_tuples(
        [
            ("battery_1", "var_battery_charge", "0"),
            ("battery_1", "var_battery_charge", "1"),
            ("battery_1", "var_battery_charge", "2"),
            ("battery_1", "var_battery_charge", "3"),
            ("battery_1", "var_battery_charge", "4"),
            ("battery_1", "var_battery_charge_mode", "0"),
            ("battery_1", "var_battery_charge_mode", "1"),
            ("battery_1", "var_battery_charge_mode", "2"),
            ("battery_1", "var_battery_charge_mode", "3"),
            ("battery_1", "var_battery_charge_mode", "4"),
            ("battery_1", "var_battery_discharge", "0"),
            ("battery_1", "var_battery_discharge", "1"),
            ("battery_1", "var_battery_discharge", "2"),
            ("battery_1", "var_battery_discharge", "3"),
            ("battery_1", "var_battery_discharge", "4"),
            ("battery_1", "var_battery_soc", "0"),
            ("battery_1", "var_battery_soc", "1"),
            ("battery_1", "var_battery_soc", "2"),
            ("battery_1", "var_battery_soc", "3"),
            ("battery_1", "var_battery_soc", "4"),
            ("generator_1", "var_generator_power", "0"),
            ("generator_1", "var_generator_power", "1"),
            ("generator_1", "var_generator_power", "2"),
            ("generator_1", "var_generator_power", "3"),
            ("generator_1", "var_generator_power", "4"),
            ("generator_2", "var_generator_power", "0"),
            ("generator_2", "var_generator_power", "1"),
            ("generator_2", "var_generator_power", "2"),
            ("generator_2", "var_generator_power", "3"),
            ("generator_2", "var_generator_power", "4"),
        ],
        names=("unit", "variable", "time"),
    )

    pd.testing.assert_index_equal(expected_index, detailed_results.index)
    pd.testing.assert_index_equal(expected_columns, detailed_results.columns)


def test_basic_results_format(energy_system_sample: EnergySystem) -> None:
    result = energy_system_sample.optimize()

    basic_results = result.to_dataframe("basic")
    expected_index = pd.Index((0, 1, 2, 3, 4), name="time")
    expected_columns = pd.Index(["battery_1", "generator_1", "generator_2"], name="unit")

    pd.testing.assert_index_equal(expected_index, basic_results.index)
    pd.testing.assert_index_equal(expected_columns, basic_results.columns)
