from datetime import timedelta

import pandas as pd
import pytest

from odis.energy_system import EnergySystem
from odis.energy_system_models.assets.generator import PowerGenerator
from odis.energy_system_models.assets.load import Load
from odis.energy_system_models.assets.portfolio import AssetPortfolio
from odis.energy_system_models.assets.storage import Battery
from odis.energy_system_models.scenarios import Scenario


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
        soc_start=100.0,
        soc_end=50.0,
    )
    load_1 = Load(name="load_1")
    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_1)
    portfolio.add_asset(generator_2)
    portfolio.add_asset(battery_1)
    portfolio.add_asset(load_1)

    demand_profile = [50, 75, 100, 125, 150]
    return EnergySystem(
        portfolio=portfolio,
        number_of_steps=len(demand_profile),
        timestep=timedelta(minutes=30),
        power_unit="MW",
        scenarios=Scenario(
            available_capacity_profiles={},
            load_profiles={"load_1": demand_profile},
        ),
    )


def test_solving_and_termination_condition(energy_system_sample: EnergySystem) -> None:
    result = energy_system_sample.optimize()
    assert result.solver_status == "ok"
    assert result.termination_condition == "optimal"


def test_detailed_results_format(energy_system_sample: EnergySystem) -> None:
    result = energy_system_sample.optimize()

    detailed_results = result.to_dataframe
    expected_columns = pd.Index(["value"])
    expected_index = pd.MultiIndex.from_tuples(
        [
            ("battery_1", "battery_charge_mode", "0"),
            ("battery_1", "battery_charge_mode", "1"),
            ("battery_1", "battery_charge_mode", "2"),
            ("battery_1", "battery_charge_mode", "3"),
            ("battery_1", "battery_charge_mode", "4"),
            ("battery_1", "battery_net_power", "0"),
            ("battery_1", "battery_net_power", "1"),
            ("battery_1", "battery_net_power", "2"),
            ("battery_1", "battery_net_power", "3"),
            ("battery_1", "battery_net_power", "4"),
            ("battery_1", "battery_power_in", "0"),
            ("battery_1", "battery_power_in", "1"),
            ("battery_1", "battery_power_in", "2"),
            ("battery_1", "battery_power_in", "3"),
            ("battery_1", "battery_power_in", "4"),
            ("battery_1", "battery_power_out", "0"),
            ("battery_1", "battery_power_out", "1"),
            ("battery_1", "battery_power_out", "2"),
            ("battery_1", "battery_power_out", "3"),
            ("battery_1", "battery_power_out", "4"),
            ("battery_1", "battery_soc", "0"),
            ("battery_1", "battery_soc", "1"),
            ("battery_1", "battery_soc", "2"),
            ("battery_1", "battery_soc", "3"),
            ("battery_1", "battery_soc", "4"),
            ("generator_1", "generator_power", "0"),
            ("generator_1", "generator_power", "1"),
            ("generator_1", "generator_power", "2"),
            ("generator_1", "generator_power", "3"),
            ("generator_1", "generator_power", "4"),
            ("generator_1", "generator_shutdown", "0"),
            ("generator_1", "generator_shutdown", "1"),
            ("generator_1", "generator_shutdown", "2"),
            ("generator_1", "generator_shutdown", "3"),
            ("generator_1", "generator_shutdown", "4"),
            ("generator_1", "generator_startup", "0"),
            ("generator_1", "generator_startup", "1"),
            ("generator_1", "generator_startup", "2"),
            ("generator_1", "generator_startup", "3"),
            ("generator_1", "generator_startup", "4"),
            ("generator_1", "generator_status", "0"),
            ("generator_1", "generator_status", "1"),
            ("generator_1", "generator_status", "2"),
            ("generator_1", "generator_status", "3"),
            ("generator_1", "generator_status", "4"),
            ("generator_2", "generator_power", "0"),
            ("generator_2", "generator_power", "1"),
            ("generator_2", "generator_power", "2"),
            ("generator_2", "generator_power", "3"),
            ("generator_2", "generator_power", "4"),
            ("generator_2", "generator_shutdown", "0"),
            ("generator_2", "generator_shutdown", "1"),
            ("generator_2", "generator_shutdown", "2"),
            ("generator_2", "generator_shutdown", "3"),
            ("generator_2", "generator_shutdown", "4"),
            ("generator_2", "generator_startup", "0"),
            ("generator_2", "generator_startup", "1"),
            ("generator_2", "generator_startup", "2"),
            ("generator_2", "generator_startup", "3"),
            ("generator_2", "generator_startup", "4"),
            ("generator_2", "generator_status", "0"),
            ("generator_2", "generator_status", "1"),
            ("generator_2", "generator_status", "2"),
            ("generator_2", "generator_status", "3"),
            ("generator_2", "generator_status", "4"),
        ],
        names=("unit", "variable", "time"),
    )

    pd.testing.assert_index_equal(expected_index, detailed_results.index)
    pd.testing.assert_index_equal(expected_columns, detailed_results.columns)
