"""EV fleet optimization with V2G and market arbitrage.

A commercial depot operates 3 delivery EVs with 2 chargers and access to a
wholesale market with time-of-use pricing. The optimizer decides when to charge,
when to discharge to the grid via vehicle-to-grid (V2G), and how to share
chargers, while guaranteeing every trip departs on time.

## Assets

- **ev_1**: 100 kWh battery, 22 kW charging, 11 kW V2G discharge. Starts at 80%
  SoC, must end at 30% SoC. 3 delivery trips throughout the day.
- **ev_2**: 60 kWh battery, 22 kW charging (no V2G). Starts at 50% SoC, must
  end at 60% SoC. 3 delivery trips.
- **ev_3**: 40 kWh battery, 7 kW charging (no V2G). Starts at 50% SoC, must end
  at 50% SoC. 2 delivery trips.
- **charger_dc**: 50 kW DC fast charger. Serves one EV at a time.
- **charger_ac**: 22 kW AC charger. Serves one EV at a time. Shared by ev_2 and
  ev_3, creating charger competition.
- **grid_market**: Buy-and-sell market with time-of-use pricing (5-100 $/MWh)
  and 100 kW max trading volume.

## Scenario

Prices swing from 5 $/MWh overnight to 100 $/MWh during the evening peak. The
fleet must complete staggered trips throughout the day while the optimizer
exploits these price differences: buying cheap overnight energy and selling it
back during expensive peaks through ev_1's V2G capability.

## Expected Results

ev_1 acts as a flexible generator during expensive hours, discharging via V2G
whenever it is parked and prices are high. ev_2 and ev_3 charge only during the
cheapest hours. With 2 chargers and 3 EVs, the optimizer dynamically assigns
vehicles to chargers based on trip deadlines and price signals, which means
charger assignments shift throughout the day to resolve contention.

## Understanding the Output

The script prints:
- EV charging/discharging power and SoC over time
- Charger assignment over time (shows which EV is connected to which charger)
- Market buy and sell volumes
- Objective value (profit, positive = revenue)

Next: see the CVaR Market Risk example to add risk-aware optimization, or the
Stochastic Optimization guide to model uncertain trip schedules.
"""

from datetime import timedelta

from odys import (
    AssetPortfolio,
    Charger,
    ElectricVehicle,
    EnergyMarket,
    EnergySystem,
    Scenario,
    TradeDirection,
    Trip,
)
from odys.results.optimization_results import OptimalDisptachResults
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)

ev_1 = ElectricVehicle(
    name="ev_1",
    capacity=0.100,
    max_charge_power=0.022,
    max_discharge_power=0.011,
    soc_start=0.8,
    soc_end=0.3,
    trips=(
        Trip(
            name="morning_delivery",
            start_time=7,
            end_time=9,
            energy_consumption=0.015,
            min_soc_at_departure=0.6,
        ),
        Trip(
            name="midday_delivery",
            start_time=11,
            end_time=12,
            energy_consumption=0.010,
            min_soc_at_departure=0.4,
        ),
        Trip(
            name="afternoon_delivery",
            start_time=14,
            end_time=16,
            energy_consumption=0.012,
            min_soc_at_departure=0.3,
        ),
    ),
)

ev_2 = ElectricVehicle(
    name="ev_2",
    capacity=0.060,
    max_charge_power=0.022,
    max_discharge_power=0.0,
    soc_start=0.5,
    soc_end=0.6,
    trips=(
        Trip(
            name="morning_route",
            start_time=8,
            end_time=10,
            energy_consumption=0.008,
            min_soc_at_departure=0.5,
        ),
        Trip(
            name="midday_route",
            start_time=12,
            end_time=13,
            energy_consumption=0.006,
            min_soc_at_departure=0.35,
        ),
        Trip(
            name="evening_route",
            start_time=17,
            end_time=19,
            energy_consumption=0.007,
            min_soc_at_departure=0.25,
        ),
    ),
)

ev_3 = ElectricVehicle(
    name="ev_3",
    capacity=0.040,
    max_charge_power=0.007,
    max_discharge_power=0.0,
    soc_start=0.5,
    soc_end=0.5,
    trips=(
        Trip(
            name="delivery_1",
            start_time=9,
            end_time=11,
            energy_consumption=0.005,
            min_soc_at_departure=0.5,
        ),
        Trip(
            name="delivery_2",
            start_time=14,
            end_time=15,
            energy_consumption=0.003,
            min_soc_at_departure=0.3,
        ),
    ),
)

EVS: tuple[ElectricVehicle, ...] = (ev_1, ev_2, ev_3)

CHARGERS: tuple[Charger, ...] = (
    Charger(name="charger_dc", max_power=0.050),
    Charger(name="charger_ac", max_power=0.022),
)

MARKET_PRICES: list[float] = [
    5.0,
    5.0,
    5.0,
    5.0,
    5.0,
    5.0,
    20.0,
    20.0,
    80.0,
    80.0,
    10.0,
    10.0,
    10.0,
    10.0,
    10.0,
    25.0,
    25.0,
    100.0,
    100.0,
    100.0,
    100.0,
    5.0,
    5.0,
    5.0,
]


def run_ev_fleet_optimization() -> OptimalDisptachResults:
    """Run the EV fleet optimization example and return the optimization results."""
    market = EnergyMarket(
        name="grid_market",
        max_trading_volume_per_step=0.100,
        trade_direction=TradeDirection.BUY_AND_SELL,
    )

    portfolio = AssetPortfolio(assets=[*EVS, *CHARGERS])

    scenario = Scenario(
        market_prices={"grid_market": MARKET_PRICES},
    )

    energy_system = EnergySystem(
        portfolio=portfolio,
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=24,
        scenarios=scenario,
    )

    return energy_system.optimize()


if __name__ == "__main__":
    result = run_ev_fleet_optimization()

    logger.info("EV charging/discharging schedules and SoC")
    for ev_name in ["ev_1", "ev_2", "ev_3"]:
        ev_data = result.electric_vehicles.to_dataset().sel(ev=ev_name)
        logger.info("%s net power (MW): %s", ev_name, ev_data.net_power.values.round(4))
        logger.info("%s SoC: %s", ev_name, ev_data.soc.values.round(3))

    logger.info("Charger assignment (1 = connected, 0 = disconnected)")
    for charger_name in ["charger_dc", "charger_ac"]:
        charger_data = result.chargers.to_dataset().sel(charger=charger_name)
        logger.info("%s assignment: %s", charger_name, charger_data.assignment.values.astype(int))

    logger.info("Market transactions (MW)")
    market_data = result.markets.to_dataset().sel(market="grid_market")
    logger.info("Buy: %s", market_data.buy_volume.values.round(4))
    logger.info("Sell: %s", market_data.sell_volume.values.round(4))

    logger.info("Objective value (profit, positive = revenue): %.4f", result.objective_value)
