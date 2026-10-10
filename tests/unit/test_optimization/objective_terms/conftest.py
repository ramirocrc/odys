"""A small two-scenario system whose profit differs by scenario, to build objective terms on."""

from collections.abc import Callable
from datetime import timedelta

import pytest

from odys.domain.entities.fixed_load import FixedLoad
from odys.domain.entities.generator import Generator
from odys.domain.entities.market import EnergyMarket
from odys.domain.entities.portfolio import AssetPortfolio
from odys.domain.objective import Objective
from odys.domain.profiles import LoadProfile, PriceProfile
from odys.domain.scenario import Scenario
from odys.energy_system import EnergySystem
from odys.optimization.problem import OptimizationProblem

GENERATOR = Generator(name="gen", nominal_power=100.0, variable_cost=20.0)
LOAD = FixedLoad(name="load")
MARKET = EnergyMarket(name="market", max_trading_volume_per_step=50.0)
DEMAND = [30.0, 40.0]
LOW_PRICES = [10.0, 15.0]
HIGH_PRICES = [60.0, 70.0]
LOW_PROBABILITY = 0.25
HIGH_PROBABILITY = 0.75


def _scenario(name: str, probability: float, prices: list[float]) -> Scenario:
    return Scenario(
        name=name,
        probability=probability,
        profiles=(LoadProfile(load=LOAD, values=DEMAND), PriceProfile(market=MARKET, values=prices)),
    )


@pytest.fixture
def problem_with() -> Callable[[Objective], OptimizationProblem]:
    """Return a builder of the problem of the two-scenario system, for a given objective."""

    def build(objective: Objective) -> OptimizationProblem:
        return EnergySystem(
            portfolio=AssetPortfolio([GENERATOR, LOAD]),
            markets=MARKET,
            timestep=timedelta(hours=1),
            number_of_steps=len(DEMAND),
            scenarios=[
                _scenario("low", LOW_PROBABILITY, LOW_PRICES),
                _scenario("high", HIGH_PROBABILITY, HIGH_PRICES),
            ],
            objective=objective,
        ).build_problem()

    return build
