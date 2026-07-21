from datetime import timedelta

import pytest

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.entities.storage import Storage
from odys.domain.scenarios import Scenario
from odys.energy_system import EnergySystem


@pytest.fixture
def energy_system_sample() -> EnergySystem:
    generator_1 = Generator(
        name="generator_1",
        nominal_power=100.0,
        variable_cost=20.0,
    )
    generator_2 = Generator(
        name="generator_2",
        nominal_power=150.0,
        variable_cost=25.0,
    )
    battery_1 = Storage(
        name="battery_1",
        max_power=200.0,
        capacity=100.0,
        efficiency_charging=1,
        efficiency_discharging=1,
        soc_start=1.0,
        soc_end=0.5,
    )
    load_1 = FixedLoad(name="load_1")
    portfolio = AssetPortfolio([generator_1, generator_2, battery_1, load_1])

    demand_profile = [50, 75, 100, 125, 150]
    return EnergySystem(
        portfolio=portfolio,
        number_of_steps=len(demand_profile),
        timestep=timedelta(minutes=30),
        scenarios=Scenario(
            available_capacity_profiles={},
            fixed_load_profiles={"load_1": demand_profile},
        ),
    )


def test_solving_and_termination_condition(energy_system_sample: EnergySystem) -> None:
    result = energy_system_sample.optimize()
    assert result.solver_status == "ok"
    assert result.termination_condition == "optimal"
