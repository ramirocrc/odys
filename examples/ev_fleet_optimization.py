"""EV fleet optimization with V2G and market arbitrage.

This example demonstrates optimizing an electric vehicle fleet with vehicle-to-grid
(V2G) capability and market arbitrage. The optimizer decides when to charge from
the grid (low prices) and when to discharge back to the grid (high prices), while
ensuring all delivery trips are completed on time.

## Assets

- **ev_1**: Large EV (100 kWh battery, 22 kW charging, 11 kW V2G). Starts at 80%
  SoC, must end at 30% SoC. Has 3 delivery trips throughout the day. V2G-capable,
  so it can discharge to the grid during expensive peak hours.
- **ev_2**: Mid-size EV (60 kWh battery, 22 kW charging). Starts at 50% SoC, must
  end at 60% SoC. Has 3 delivery trips. Charge-only (no V2G).
- **ev_3**: Small EV (40 kWh battery, 7 kW charging). Starts at 50% SoC, must end
  at 50% SoC. Has 2 delivery trips. Charge-only (no V2G).
- **charger_dc**: 50 kW DC fast charger. Can serve one EV at a time. Used by ev_1
  for V2G operations.
- **charger_ac**: 22 kW AC charger. Can serve one EV at a time. Shared by ev_2 and
  ev_3 (charger competition).
- **grid_market**: Buy-and-sell electricity market with time-of-use pricing.
  Max 100 kW trading volume per timestep.

## Scenario

A commercial depot with 3 delivery EVs and 2 chargers. The operator wants to
minimize electricity costs (or maximize revenue from V2G) over a 24-hour horizon
while ensuring all trips are completed on time.

## Time-of-Use Pricing

The market has clear price signals that drive charging and V2G behavior:

- Overnight (t0-t5): 5/MWh — very cheap, charge here
- Morning ramp (t6-t7): 20/MWh — moderate, V2G discharge here if parked
- Morning peak (t8-t9): 80/MWh — expensive, V2G discharge here
- Midday (t10-t14): 10/MWh — cheap, recharge here
- Evening ramp (t15-t16): 25/MWh — moderate, V2G discharge here if parked
- Evening peak (t17-t20): 100/MWh — very expensive, V2G discharge here
- Late evening (t21-t23): 5/MWh — cheap again

## Expected Optimizer Behavior

1. **ev_1 (V2G)**: Charges overnight (t0-t5), discharges to the grid via V2G
   during the morning ramp (t6-t7), morning peak (t8-t9), evening ramp
   (t15-t16), and evening peak (t17-t20) when parked at the depot, recharges
   during cheap midday hours, completes 3 trips. Starts at 80% SoC, ends at 30%.

2. **ev_2 (charge-only)**: Charges before morning trip, avoids peak charging,
   charges during midday between trips. Must share charger_ac with ev_3.

3. **ev_3 (charge-only)**: Charges at cheapest hours around its trips. Must share
   charger_ac with ev_2 (charger competition).

4. **Charger competition**: With 2 chargers and 3 EVs, ev_2 and ev_3 must take
   turns on charger_ac. The optimizer prioritizes based on trip deadlines and
   price signals.

5. **Market arbitrage**: The depot buys electricity at 5-10/MWh and sells at
   20-100/MWh via ev_1's V2G capability, potentially generating revenue.

## Understanding the Output

The script prints:
- EV charging/discharging power and SoC over time
- Charger assignment over time (shows which EV is connected to which charger)
- Market buy and sell volumes
- Objective value (profit, positive = revenue)

This example demonstrates V2G arbitrage, charger competition, and complex trip
scheduling in a realistic EV fleet optimization scenario.
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
