"""Scenario profiles reach each formulation in coordinate order, with defaults for missing profiles."""

from datetime import timedelta

import numpy as np
import pytest
import xarray as xr

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.profiles import AvailableCapacityProfile, LoadProfile, PriceProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.formulations.energy_market import EnergyMarketFormulation
from odys.optimization.formulations.flexible_load import FlexibleLoadFormulation
from odys.optimization.formulations.generator import GeneratorFormulation
from odys.optimization.problem import OptimizationProblem

NUMBER_OF_STEPS = 2
NOMINAL_POWER = 500.0
VARIABLE_COST = 10.0
MAX_TRADING_VOLUME = 500.0
FIRST_LOAD = [10.0, 20.0]
SECOND_LOAD = [1.0, 2.0]
FLEX_BASE = [50.0, 60.0]
LOW_PRICES = [5.0, 6.0]
HIGH_PRICES = [50.0, 60.0]
CAPACITY = [100.0, 200.0]
HALF = 0.5


@pytest.fixture
def first_load() -> FixedLoad:
    return FixedLoad(name="load_a")


@pytest.fixture
def second_load() -> FixedLoad:
    return FixedLoad(name="load_b")


@pytest.fixture
def flexible_load() -> FlexibleLoad:
    return FlexibleLoad(name="flex", max_increase=5.0, max_decrease=5.0, value_of_consumption=40.0)


@pytest.fixture
def generators() -> tuple[Generator, Generator]:
    return (
        Generator(name="gen_a", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST),
        Generator(name="gen_b", nominal_power=NOMINAL_POWER, variable_cost=VARIABLE_COST),
    )


@pytest.fixture
def markets() -> tuple[EnergyMarket, EnergyMarket]:
    return (
        EnergyMarket(name="market_a", max_trading_volume_per_step=MAX_TRADING_VOLUME),
        EnergyMarket(name="market_b", max_trading_volume_per_step=MAX_TRADING_VOLUME),
    )


@pytest.fixture
def optimization_problem(
    first_load: FixedLoad,
    second_load: FixedLoad,
    flexible_load: FlexibleLoad,
    generators: tuple[Generator, Generator],
    markets: tuple[EnergyMarket, EnergyMarket],
) -> OptimizationProblem:
    gen_a, gen_b = generators
    market_a, market_b = markets
    shuffled_profiles = (
        PriceProfile(market=market_b, values=HIGH_PRICES),
        LoadProfile(load=second_load, values=SECOND_LOAD),
        AvailableCapacityProfile(generator=gen_b, values=CAPACITY),
        LoadProfile(load=flexible_load, values=FLEX_BASE),
        PriceProfile(market=market_a, values=LOW_PRICES),
        LoadProfile(load=first_load, values=FIRST_LOAD),
    )
    energy_system = EnergySystem(
        portfolio=AssetPortfolio([gen_a, gen_b, first_load, second_load, flexible_load]),
        markets=markets,
        timestep=timedelta(hours=1),
        number_of_steps=NUMBER_OF_STEPS,
        scenarios=[
            Scenario(name="s1", probability=HALF, profiles=shuffled_profiles),
            Scenario(name="s2", probability=HALF, profiles=shuffled_profiles),
        ],
    )
    return energy_system.build_problem()


def _expected(data: list[list[float]], entity_dimension: str, entities: list[str]) -> xr.DataArray:
    return xr.DataArray(
        data=[data, data],
        coords={"scenario": ["s1", "s2"], entity_dimension: entities, "time": ["0", "1"]},
    )


def test_market_prices_follow_coordinate_order_not_profile_order(optimization_problem: OptimizationProblem) -> None:
    markets = optimization_problem.formulation_of(EnergyMarketFormulation)
    assert markets is not None
    xr.testing.assert_allclose(
        markets.prices,
        _expected([LOW_PRICES, HIGH_PRICES], "market", ["market_a", "market_b"]),
    )


def test_generator_without_profile_is_unbounded(optimization_problem: OptimizationProblem) -> None:
    generators = optimization_problem.formulation_of(GeneratorFormulation)
    assert generators is not None
    xr.testing.assert_allclose(
        generators.available_capacity,
        _expected([[np.inf, np.inf], CAPACITY], "generator", ["gen_a", "gen_b"]),
    )


def test_flexible_load_base_profiles(optimization_problem: OptimizationProblem) -> None:
    flexible_loads = optimization_problem.formulation_of(FlexibleLoadFormulation)
    assert flexible_loads is not None
    xr.testing.assert_allclose(
        flexible_loads.base_profiles,
        _expected([FLEX_BASE], "flexible_load", ["flex"]),
    )


def test_formulations_absent_without_matching_entities(first_load: FixedLoad) -> None:
    grid = EnergyMarket(name="grid", max_trading_volume_per_step=MAX_TRADING_VOLUME)
    energy_system = EnergySystem(
        portfolio=AssetPortfolio([first_load]),
        markets=grid,
        timestep=timedelta(hours=1),
        number_of_steps=NUMBER_OF_STEPS,
        scenarios=Scenario(
            profiles=(
                LoadProfile(load=first_load, values=FIRST_LOAD),
                PriceProfile(market=grid, values=LOW_PRICES),
            ),
        ),
    )
    problem = energy_system.build_problem()

    assert problem.formulation_of(GeneratorFormulation) is None
    assert problem.formulation_of(FlexibleLoadFormulation) is None
