from datetime import timedelta

import pytest

from odys.domain.entities.battery import Battery
from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.stationary_storage import StationaryStorage
from odys.domain.profiles import AvailableCapacityProfile, LoadProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem


@pytest.fixture
def wind_generator() -> Generator:
    return Generator(
        name="wind_farm",
        nominal_power=150.0,
        variable_cost=10.0,
    )


@pytest.fixture
def gas_generator() -> Generator:
    return Generator(
        name="gas_plant",
        nominal_power=100.0,
        variable_cost=50.0,
    )


@pytest.fixture
def battery() -> StationaryStorage:
    return StationaryStorage(
        name="stationary_storage",
        battery=Battery(
            capacity=100.0,
            max_charge_power=80.0,
            max_discharge_power=80.0,
            efficiency_charging=0.9,
            efficiency_discharging=0.9,
            soc_start=0.5,
            soc_end=0.5,
        ),
    )


@pytest.fixture
def load() -> FixedLoad:
    return FixedLoad(name="load1")


@pytest.fixture
def portfolio_with_battery(
    wind_generator: Generator,
    gas_generator: Generator,
    battery: StationaryStorage,
    load: FixedLoad,
) -> AssetPortfolio:
    return AssetPortfolio([wind_generator, gas_generator, battery, load])


@pytest.fixture
def portfolio_without_battery(
    wind_generator: Generator,
    gas_generator: Generator,
    load: FixedLoad,
) -> AssetPortfolio:
    return AssetPortfolio([wind_generator, gas_generator, load])


@pytest.fixture
def scenarios(wind_generator: Generator, gas_generator: Generator, load: FixedLoad) -> list[Scenario]:
    return [
        Scenario(
            name="high_wind",
            probability=0.6,
            profiles=(
                AvailableCapacityProfile(generator=wind_generator, values=[150.0, 120.0, 100.0]),
                AvailableCapacityProfile(generator=gas_generator, values=[100.0, 100.0, 100.0]),
                LoadProfile(load=load, values=[120.0, 100.0, 80.0]),
            ),
        ),
        Scenario(
            name="low_wind",
            probability=0.4,
            profiles=(
                AvailableCapacityProfile(generator=wind_generator, values=[50.0, 30.0, 20.0]),
                AvailableCapacityProfile(generator=gas_generator, values=[100.0, 100.0, 100.0]),
                LoadProfile(load=load, values=[120.0, 100.0, 80.0]),
            ),
        ),
    ]


@pytest.fixture
def demand_profile() -> list[float]:
    return [120.0, 100.0, 80.0]


def test_two_scenario_optimization_with_anticipativity(
    portfolio_with_battery: AssetPortfolio,
    scenarios: list[Scenario],
    demand_profile: list[float],
) -> None:
    energy_system_anticipative = EnergySystem(
        portfolio=portfolio_with_battery,
        timestep=timedelta(hours=1),
        number_of_steps=len(demand_profile),
        scenarios=scenarios,
    )

    result_anticipative = energy_system_anticipative.optimize()

    assert result_anticipative.solver_status == "ok"
    assert result_anticipative.termination_condition == "optimal"


def test_two_scenario_optimization_with_non_anticipativity(
    portfolio_with_battery: AssetPortfolio,
    scenarios: list[Scenario],
    demand_profile: list[float],
) -> None:
    energy_system_non_anticipative = EnergySystem(
        portfolio=portfolio_with_battery,
        timestep=timedelta(hours=1),
        number_of_steps=len(demand_profile),
        scenarios=scenarios,
    )

    result_non_anticipative = energy_system_non_anticipative.optimize()

    assert result_non_anticipative.solver_status == "ok"
    assert result_non_anticipative.termination_condition == "optimal"


def test_anticipativity_vs_non_anticipativity_comparison(
    portfolio_without_battery: AssetPortfolio,
    scenarios: list[Scenario],
    demand_profile: list[float],
) -> None:
    energy_system = EnergySystem(
        portfolio=portfolio_without_battery,
        timestep=timedelta(hours=1),
        number_of_steps=len(demand_profile),
        scenarios=scenarios,
    )

    result_anticipative = energy_system.optimize()
    result_non_anticipative = energy_system.optimize()

    assert result_anticipative.solver_status == "ok"
    assert result_non_anticipative.solver_status == "ok"
    assert result_anticipative.termination_condition == "optimal"
    assert result_non_anticipative.termination_condition == "optimal"

    # todo: compare objective value and check that non-anticipativity is more expensive
