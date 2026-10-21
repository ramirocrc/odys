"""Objective terms priced per MWh must scale with the timestep length."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta

import pytest

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.flexible_load import FlexibleLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import AllowedTradeDirection, EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.profiles import FlexibleLoadProfile, LoadProfile, PriceProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem

HALF_HOUR = timedelta(minutes=30)
HALF_HOUR_IN_HOURS = 0.5

GENERATOR_POWER = 100.0
GENERATOR_COST = 20.0
LOAD_PROFILE = [50.0, 100.0]

MARKET_VOLUME = 200.0
MARKET_PRICES = [30.0, 40.0]

FLEXIBLE_LOWER_BOUND = [40.0, 40.0]
FLEXIBLE_UPPER_BOUND = [60.0, 60.0]
VALUE_OF_CONSUMPTION = 30.0


@dataclass(frozen=True)
class TimestepCase:
    energy_system: EnergySystem
    expected_objective: float


def generator_serving_fixed_load() -> TimestepCase:
    load = FixedLoad(name="load")
    energy_system = EnergySystem(
        portfolio=AssetPortfolio(
            [Generator(name="gen", nominal_power=GENERATOR_POWER, variable_cost=GENERATOR_COST), load],
        ),
        timestep=HALF_HOUR,
        number_of_steps=len(LOAD_PROFILE),
        scenarios=Scenario(profiles=(LoadProfile(load=load, values=LOAD_PROFILE),)),
    )
    expected_cost = sum(LOAD_PROFILE) * HALF_HOUR_IN_HOURS * GENERATOR_COST
    return TimestepCase(energy_system=energy_system, expected_objective=-expected_cost)


def market_serving_fixed_load() -> TimestepCase:
    load = FixedLoad(name="load")
    market = EnergyMarket(
        name="market",
        max_trading_volume_per_step=MARKET_VOLUME,
        allowed_trade_direction=AllowedTradeDirection.BUY_ONLY,
    )
    energy_system = EnergySystem(
        portfolio=AssetPortfolio([load]),
        markets=market,
        timestep=HALF_HOUR,
        number_of_steps=len(LOAD_PROFILE),
        scenarios=Scenario(
            profiles=(LoadProfile(load=load, values=LOAD_PROFILE), PriceProfile(market=market, values=MARKET_PRICES)),
        ),
    )
    expected_cost = sum(
        load * price * HALF_HOUR_IN_HOURS for load, price in zip(LOAD_PROFILE, MARKET_PRICES, strict=True)
    )
    return TimestepCase(energy_system=energy_system, expected_objective=-expected_cost)


def flexible_load_increasing_consumption() -> TimestepCase:
    flexible_load = FlexibleLoad(name="flex", value_of_consumption=VALUE_OF_CONSUMPTION)
    flexible_range = FlexibleLoadProfile(
        load=flexible_load,
        lower_bound=FLEXIBLE_LOWER_BOUND,
        upper_bound=FLEXIBLE_UPPER_BOUND,
    )
    energy_system = EnergySystem(
        portfolio=AssetPortfolio(
            [Generator(name="gen", nominal_power=GENERATOR_POWER, variable_cost=GENERATOR_COST), flexible_load],
        ),
        timestep=HALF_HOUR,
        number_of_steps=len(FLEXIBLE_UPPER_BOUND),
        scenarios=Scenario(profiles=(flexible_range,)),
    )
    expected_objective = sum(
        HALF_HOUR_IN_HOURS * upper_bound * (VALUE_OF_CONSUMPTION - GENERATOR_COST)
        for upper_bound in FLEXIBLE_UPPER_BOUND
    )
    return TimestepCase(energy_system=energy_system, expected_objective=expected_objective)


@pytest.mark.parametrize(
    "case_factory",
    [generator_serving_fixed_load, market_serving_fixed_load, flexible_load_increasing_consumption],
    ids=["generator_cost", "market_cost", "flexible_load_value"],
)
def test_objective_scales_energy_terms_with_timestep_length(case_factory: Callable[[], TimestepCase]) -> None:
    case = case_factory()
    result = case.energy_system.optimize()
    assert result.objective_value == pytest.approx(case.expected_objective)
