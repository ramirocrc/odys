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
from odys.domain.scenarios import Scenario
from odys.energy_system import EnergySystem

HALF_HOUR = timedelta(minutes=30)
HALF_HOUR_IN_HOURS = 0.5

GENERATOR_POWER = 100.0
GENERATOR_COST = 20.0
LOAD_PROFILE = [50.0, 100.0]

MARKET_VOLUME = 200.0
MARKET_PRICES = [30.0, 40.0]

FLEXIBLE_BASE_PROFILE = [50.0, 50.0]
FLEXIBLE_MAX_CHANGE = 10.0
VALUE_OF_CONSUMPTION = 30.0


@dataclass(frozen=True)
class TimestepCase:
    energy_system: EnergySystem
    expected_objective: float


def generator_serving_fixed_load() -> TimestepCase:
    energy_system = EnergySystem(
        portfolio=AssetPortfolio(
            [
                Generator(name="gen", nominal_power=GENERATOR_POWER, variable_cost=GENERATOR_COST),
                FixedLoad(name="load"),
            ],
        ),
        timestep=HALF_HOUR,
        number_of_steps=len(LOAD_PROFILE),
        scenarios=Scenario(fixed_load_profiles={"load": LOAD_PROFILE}),
    )
    expected_cost = sum(LOAD_PROFILE) * HALF_HOUR_IN_HOURS * GENERATOR_COST
    return TimestepCase(energy_system=energy_system, expected_objective=-expected_cost)


def market_serving_fixed_load() -> TimestepCase:
    energy_system = EnergySystem(
        portfolio=AssetPortfolio([FixedLoad(name="load")]),
        markets=EnergyMarket(
            name="market",
            max_trading_volume_per_step=MARKET_VOLUME,
            allowed_trade_direction=AllowedTradeDirection.BUY_ONLY,
        ),
        timestep=HALF_HOUR,
        number_of_steps=len(LOAD_PROFILE),
        scenarios=Scenario(
            fixed_load_profiles={"load": LOAD_PROFILE},
            market_prices={"market": MARKET_PRICES},
        ),
    )
    expected_cost = sum(
        load * price * HALF_HOUR_IN_HOURS for load, price in zip(LOAD_PROFILE, MARKET_PRICES, strict=True)
    )
    return TimestepCase(energy_system=energy_system, expected_objective=-expected_cost)


def flexible_load_increasing_consumption() -> TimestepCase:
    energy_system = EnergySystem(
        portfolio=AssetPortfolio(
            [
                Generator(name="gen", nominal_power=GENERATOR_POWER, variable_cost=GENERATOR_COST),
                FlexibleLoad(
                    name="flex",
                    max_increase=FLEXIBLE_MAX_CHANGE,
                    max_decrease=FLEXIBLE_MAX_CHANGE,
                    value_of_consumption=VALUE_OF_CONSUMPTION,
                ),
            ],
        ),
        timestep=HALF_HOUR,
        number_of_steps=len(FLEXIBLE_BASE_PROFILE),
        scenarios=Scenario(flexible_load_base_profiles={"flex": FLEXIBLE_BASE_PROFILE}),
    )
    expected_objective = sum(
        HALF_HOUR_IN_HOURS
        * (FLEXIBLE_MAX_CHANGE * VALUE_OF_CONSUMPTION - (base + FLEXIBLE_MAX_CHANGE) * GENERATOR_COST)
        for base in FLEXIBLE_BASE_PROFILE
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
