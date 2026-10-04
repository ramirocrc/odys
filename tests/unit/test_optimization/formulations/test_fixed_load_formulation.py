"""Unit tests for the fixed-load formulation."""

from datetime import timedelta

import linopy
import pytest
import xarray as xr

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.profiles import LoadProfile, PriceProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations.fixed_load import FixedLoadFormulation
from odys.optimization.problem import OptimizationProblem

NUMBER_OF_STEPS = 2
HALF = 0.5
FIRST_LOAD = [10.0, 20.0]
SECOND_LOAD = [1.0, 2.0]
NOMINAL_POWER = 500.0
MAX_TRADING_VOLUME = 500.0
PRICES = [5.0, 6.0]

FIRST = FixedLoad(name="load_a")
SECOND = FixedLoad(name="load_b")
GENERATOR = Generator(name="gen", nominal_power=NOMINAL_POWER, variable_cost=1.0)


def _problem(portfolio: AssetPortfolio, *scenarios: Scenario) -> OptimizationProblem:
    return EnergySystem(
        portfolio=portfolio,
        timestep=timedelta(hours=1),
        number_of_steps=NUMBER_OF_STEPS,
        scenarios=list(scenarios),
    ).build_problem()


@pytest.fixture
def formulation() -> FixedLoadFormulation:
    profiles = (LoadProfile(load=SECOND, values=SECOND_LOAD), LoadProfile(load=FIRST, values=FIRST_LOAD))
    problem = _problem(
        AssetPortfolio([GENERATOR, FIRST, SECOND]),
        Scenario(name="s1", probability=HALF, profiles=profiles),
        Scenario(name="s2", probability=HALF, profiles=profiles),
    )
    fixed_loads = problem.formulation_of(FixedLoadFormulation)
    assert fixed_loads is not None
    return fixed_loads


def test_fixed_load_power_injection_is_minus_the_demand_summed_over_loads(formulation: FixedLoadFormulation) -> None:
    total_demand = [first + second for first, second in zip(FIRST_LOAD, SECOND_LOAD, strict=True)]
    expected = xr.DataArray(
        data=[total_demand, total_demand],
        coords={"scenario": ["s1", "s2"], "time": ["0", "1"]},
    )
    xr.testing.assert_allclose(formulation.power_injection(), -expected)


def test_fixed_load_has_no_variables_constraints_or_profit(formulation: FixedLoadFormulation) -> None:
    model = linopy.Model(force_dim_names=True)

    formulation.add_variables(model)

    assert not model.variables
    assert formulation.collect_constraints() == []
    assert formulation.profit() is None


def test_fixed_load_formulation_is_absent_without_fixed_loads() -> None:
    market = EnergyMarket(name="market", max_trading_volume_per_step=MAX_TRADING_VOLUME)
    problem = EnergySystem(
        portfolio=AssetPortfolio([GENERATOR]),
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=NUMBER_OF_STEPS,
        scenarios=Scenario(profiles=(PriceProfile(market=market, values=PRICES),)),
    ).build_problem()

    assert problem.formulation_of(FixedLoadFormulation) is None
