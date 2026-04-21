"""Example: Multi-stage stochastic dispatch optimization."""

from datetime import timedelta

from odys import (
    AssetPortfolio,
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
    ccgt_unit = Generator(
        name="ccgt",
        nominal_power=100.0,
        variable_cost=20.0,
    )

    portfolio = AssetPortfolio(assets=[ccgt_unit])

    sdac_market = EnergyMarket(
        name="sdac",
        max_trading_volume_per_step=150,
        stage_fixed=True,
        trade_direction=TradeDirection.SELL_ONLY,
    )
    sidc_market = EnergyMarket(
        name="sidc",
        max_trading_volume_per_step=100,
        trade_direction=TradeDirection.SELL_ONLY,
    )
    energy_system = EnergySystem(
        portfolio=portfolio,
        markets=[sdac_market, sidc_market],
        scenarios=[
            StochasticScenario(
                name="scenario_1",
                probability=0.51,
                available_capacity_profiles={
                    "ccgt": 8 * [100],
                },
                market_prices={
                    "sdac": 8 * [200],
                    "sidc": [190, 190, 190, 190, 190, 190, 190, 190],
                },
            ),
            StochasticScenario(
                name="scenario_2",
                probability=0.49,
                available_capacity_profiles={
                    "ccgt": 8 * [100],
                },
                market_prices={
                    "sdac": 8 * [200],
                    "sidc": [210, 210, 210, 210, 210, 210, 210, 210],
                },
            ),
        ],
        timestep=timedelta(minutes=30),
        objective=Objective(
            profit=ProfitTerm(weight=1),
        ),
        number_of_steps=8,
    )

    result = energy_system.optimize(solver_config=SolverConfig(solver_name=SolverName.HIGHS))
    logger.info(result.termination_condition)
    logger.info(result.solver_status)
    logger.info("solution dataframe")
    logger.info(result.to_dataset())
