from datetime import timedelta

import pandas as pd

from optimes.energy_system import EnergySystem
from optimes.energy_system_models.assets.generator import PowerGenerator
from optimes.energy_system_models.assets.portfolio import AssetPortfolio
from optimes.energy_system_models.assets.storage import Battery


def test_single_generator_meets_demand() -> None:
    generator = PowerGenerator(
        name="generator",
        nominal_power=200.0,
        variable_cost=30.0,
    )

    portfolio = AssetPortfolio()
    portfolio.add_asset(generator)

    demand_profile = [50.0, 100.0, 150.0, 180.0, 120.0]
    timestep = timedelta(hours=1)

    expected_results = pd.DataFrame(
        {"generator": demand_profile},
        index=pd.MultiIndex.from_product(
            [["deterministic_scenario"], ["0", "1", "2", "3", "4"]],
            names=["scenario", "time"],
        ),
    )
    expected_results.columns.name = "generator"

    energy_system = EnergySystem(
        portfolio=portfolio,
        demand_profile=demand_profile,
        timestep=timestep,
        power_unit="MW",
    )
    result = energy_system.optimize()
    generator_power = result.generators.power
    assert result.solver_status == "ok"
    assert result.termination_condition == "optimal"

    pd.testing.assert_frame_equal(generator_power, expected_results)


def test_three_generators_meet_demand() -> None:
    generator_cheap = PowerGenerator(
        name="generator_100mw_cheap",
        nominal_power=100.0,
        variable_cost=20.0,
    )
    generator_medium = PowerGenerator(
        name="generator_100mw_medium",
        nominal_power=100.0,
        variable_cost=30.0,
    )
    generator_expensive = PowerGenerator(
        name="generator_100mw_expensive",
        nominal_power=100.0,
        variable_cost=40.0,
    )

    portfolio = AssetPortfolio()
    portfolio.add_asset(generator_cheap)
    portfolio.add_asset(generator_medium)
    portfolio.add_asset(generator_expensive)

    demand_profile = [50.0, 100.0, 150.0, 200.0, 250.0, 300.0]
    timestep = timedelta(hours=1)

    expected_results = pd.DataFrame(
        {
            generator_cheap.name: [50.0, 100.0, 100.0, 100.0, 100.0, 100.0],
            generator_medium.name: [0.0, 0.0, 50.0, 100.0, 100.0, 100.0],
            generator_expensive.name: [0.0, 0.0, 0.0, 0.0, 50.0, 100.0],
        },
        index=pd.MultiIndex.from_product(
            [["deterministic_scenario"], ["0", "1", "2", "3", "4", "5"]],
            names=["scenario", "time"],
        ),
    )
    expected_results.columns.name = "generator"

    energy_system = EnergySystem(
        portfolio=portfolio,
        demand_profile=demand_profile,
        timestep=timestep,
        power_unit="MW",
    )

    result = energy_system.optimize()
    generator_power = result.generators.power

    pd.testing.assert_frame_equal(generator_power, expected_results)


def test_generator_and_battery_optimization() -> None:
    generator = PowerGenerator(
        name="base_generator",
        nominal_power=100.0,
        variable_cost=25.0,
    )
    battery = Battery(
        name="energy_storage",
        capacity=100.0,
        max_power=100.0,
        efficiency_charging=1.0,
        efficiency_discharging=1.0,
        soc_start=0.0,
        soc_end=50.0,
    )

    portfolio = AssetPortfolio()
    portfolio.add_asset(generator)
    portfolio.add_asset(battery)

    demand_profile = [50.0, 50.0, 150.0, 150.0, 50.0]
    index = pd.MultiIndex.from_product(
        [["deterministic_scenario"], ["0", "1", "2", "3", "4"]],
        names=["scenario", "time"],
    )
    expected_generator_results = pd.DataFrame(
        {
            generator.name: [100.0, 100.0, 100.0, 100.0, 100.0],
        },
        index=index,
    )
    expected_battery_soc_results = pd.DataFrame(
        {
            battery.name: [50.0, 100.0, 50.0, 0.0, 50.0],
        },
        index=index,
    )
    expected_generator_results.columns.name = "generator"
    expected_battery_soc_results.columns.name = "battery"
    timestep = timedelta(hours=1)

    energy_system = EnergySystem(
        portfolio=portfolio,
        demand_profile=demand_profile,
        timestep=timestep,
        power_unit="MW",
    )

    result = energy_system.optimize()
    generator_power = result.generators.power
    battery_soc = result.batteries.state_of_charge

    pd.testing.assert_frame_equal(generator_power, expected_generator_results)
    pd.testing.assert_frame_equal(battery_soc, expected_battery_soc_results)


def test_generator_and_battery_with_efficiencies_optimization() -> None:
    generator = PowerGenerator(
        name="generator",
        nominal_power=100.0,
        variable_cost=25.0,
    )
    battery = Battery(
        name="battery",
        capacity=100.0,
        max_power=100.0,
        efficiency_charging=0.5,
        efficiency_discharging=0.5,
        soc_start=0.0,
        soc_end=50.0,
    )

    portfolio = AssetPortfolio()
    portfolio.add_asset(generator)
    portfolio.add_asset(battery)

    demand_profile = [50.0, 50.0, 100.0]
    timestep = timedelta(hours=1)

    index = pd.MultiIndex.from_product(
        [["deterministic_scenario"], ["0", "1", "2"]],
        names=["scenario", "time"],
    )
    expected_generator_results = pd.DataFrame(
        {
            generator.name: [100.0, 100.0, 100.0],
        },
        index=index,
    )
    expected_battery_soc_results = pd.DataFrame(
        {
            battery.name: [25.0, 50.0, 50.0],
        },
        index=index,
    )
    expected_generator_results.columns.name = "generator"
    expected_battery_soc_results.columns.name = "battery"

    energy_system = EnergySystem(
        portfolio=portfolio,
        demand_profile=demand_profile,
        timestep=timestep,
        power_unit="MW",
    )
    result = energy_system.optimize()
    generator_power = result.generators.power
    battery_soc = result.batteries.state_of_charge

    pd.testing.assert_frame_equal(generator_power, expected_generator_results)
    pd.testing.assert_frame_equal(battery_soc, expected_battery_soc_results)
