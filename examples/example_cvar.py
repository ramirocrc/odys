"""Example: CVaR optimization with multiple markets."""

from datetime import timedelta

from odys import (
    AssetPortfolio,
    CVaRTerm,
    EnergyMarket,
    EnergySystem,
    Generator,
    Objective,
    ProfitTerm,
    SolverConfig,
    SolverName,
    StochasticScenario,
    TradeDirection,
)
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=20.0)

    portfolio = AssetPortfolio(assets=[ccgt])

    sdac = EnergyMarket(
        name="sdac",
        max_trading_volume_per_step=150,
        stage_fixed=True,
        trade_direction=TradeDirection.SELL_ONLY,
    )
    sidc = EnergyMarket(
        name="sidc",
        max_trading_volume_per_step=100,
        trade_direction=TradeDirection.SELL_ONLY,
    )

    energy_system = EnergySystem(
        portfolio=portfolio,
        markets=[sdac, sidc],
        scenarios=[
            StochasticScenario(
                name="high",
                probability=1 / 3,
                available_capacity_profiles={"ccgt": 4 * [100]},
                market_prices={"sdac": 4 * [200], "sidc": 4 * [500]},
            ),
            StochasticScenario(
                name="mid",
                probability=1 / 3,
                available_capacity_profiles={"ccgt": 4 * [100]},
                market_prices={"sdac": 4 * [200], "sidc": 4 * [200]},
            ),
            StochasticScenario(
                name="low",
                probability=1 / 3,
                available_capacity_profiles={"ccgt": 4 * [100]},
                market_prices={"sdac": 4 * [200], "sidc": 4 * [15]},
            ),
        ],
        timestep=timedelta(minutes=30),
        number_of_steps=4,
        objective=Objective(
            profit=ProfitTerm(weight=1),
            cvar=CVaRTerm(weight=100, confidence_level=0.6),
        ),
    )
    solver_config = SolverConfig(
        solver_name=SolverName.HIGHS,
        log_output=False,
    )
    result = energy_system.optimize(solver_config=solver_config)

    logger.info("solution dataframe")
    logger.info(result.to_dataset())
