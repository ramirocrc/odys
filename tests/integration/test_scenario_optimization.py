from datetime import timedelta

import pytest

from odis.energy_system import EnergySystem
from odis.energy_system_models.assets.generator import PowerGenerator
from odis.energy_system_models.assets.load import Load
from odis.energy_system_models.assets.portfolio import AssetPortfolio
from odis.energy_system_models.assets.storage import Battery
from odis.energy_system_models.scenarios import StochasticScenario


@pytest.fixture
def wind_generator() -> PowerGenerator:
    return PowerGenerator(
        name="wind_farm",
        nominal_power=150.0,
        variable_cost=10.0,
    )


@pytest.fixture
def gas_generator() -> PowerGenerator:
    return PowerGenerator(
        name="gas_plant",
        nominal_power=100.0,
        variable_cost=50.0,
    )


@pytest.fixture
def battery() -> Battery:
    return Battery(
        name="storage",
        capacity=100.0,
        max_power=80.0,
        efficiency_charging=0.9,
        efficiency_discharging=0.9,
        soc_start=50.0,
        soc_end=50.0,
    )


@pytest.fixture
def load() -> Load:
    return Load(name="load1")


@pytest.fixture
def portfolio_with_battery(
    wind_generator: PowerGenerator,
    gas_generator: PowerGenerator,
    battery: Battery,
    load: Load,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(wind_generator)
    portfolio.add_asset(gas_generator)
    portfolio.add_asset(battery)
    portfolio.add_asset(load)
    return portfolio


@pytest.fixture
def portfolio_without_battery(
    wind_generator: PowerGenerator,
    gas_generator: PowerGenerator,
    load: Load,
) -> AssetPortfolio:
    portfolio = AssetPortfolio()
    portfolio.add_asset(wind_generator)
    portfolio.add_asset(gas_generator)
    portfolio.add_asset(load)
    return portfolio


@pytest.fixture
def scenarios() -> list[StochasticScenario]:
    return [
        StochasticScenario(
            name="high_wind",
            probability=0.6,
            available_capacity_profiles={
                "wind_farm": [150.0, 120.0, 100.0],
                "gas_plant": [100.0, 100.0, 100.0],
            },
            load_profiles={
                "load1": [120.0, 100.0, 80.0],
            },
        ),
        StochasticScenario(
            name="low_wind",
            probability=0.4,
            available_capacity_profiles={
                "wind_farm": [50.0, 30.0, 20.0],
                "gas_plant": [100.0, 100.0, 100.0],
            },
            load_profiles={
                "load1": [120.0, 100.0, 80.0],
            },
        ),
    ]


@pytest.fixture
def demand_profile() -> list[float]:
    return [120.0, 100.0, 80.0]


def test_two_scenario_optimization_with_anticipativity(
    portfolio_with_battery: AssetPortfolio,
    scenarios: list[StochasticScenario],
    demand_profile: list[float],
) -> None:
    energy_system_anticipative = EnergySystem(
        portfolio=portfolio_with_battery,
        timestep=timedelta(hours=1),
        number_of_steps=len(demand_profile),
        scenarios=scenarios,
        power_unit="MW",
    )

    result_anticipative = energy_system_anticipative.optimize()

    assert result_anticipative.solver_status == "ok"
    assert result_anticipative.termination_condition == "optimal"


def test_two_scenario_optimization_with_non_anticipativity(
    portfolio_with_battery: AssetPortfolio,
    scenarios: list[StochasticScenario],
    demand_profile: list[float],
) -> None:
    energy_system_non_anticipative = EnergySystem(
        portfolio=portfolio_with_battery,
        timestep=timedelta(hours=1),
        number_of_steps=len(demand_profile),
        scenarios=scenarios,
        power_unit="MW",
    )

    result_non_anticipative = energy_system_non_anticipative.optimize()

    assert result_non_anticipative.solver_status == "ok"
    assert result_non_anticipative.termination_condition == "optimal"


def test_anticipativity_vs_non_anticipativity_comparison(
    portfolio_without_battery: AssetPortfolio,
    scenarios: list[StochasticScenario],
    demand_profile: list[float],
) -> None:
    energy_system = EnergySystem(
        portfolio=portfolio_without_battery,
        timestep=timedelta(hours=1),
        number_of_steps=len(demand_profile),
        scenarios=scenarios,
        power_unit="MW",
    )

    result_anticipative = energy_system.optimize()
    result_non_anticipative = energy_system.optimize()

    assert result_anticipative.solver_status == "ok"
    assert result_non_anticipative.solver_status == "ok"
    assert result_anticipative.termination_condition == "optimal"
    assert result_non_anticipative.termination_condition == "optimal"

    # todo: compare objective value and check that non-anticipativity is more expensive
