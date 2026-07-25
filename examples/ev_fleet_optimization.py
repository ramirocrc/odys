"""EV fleet optimization with chargers, solar PV, and market participation.

This example demonstrates how to optimize an electric vehicle fleet with
individual trip schedules, explicit charger assignment, and grid market
participation. It also includes a stationary battery to show how EVs and
stationary storage can coexist in the same optimization.

## Assets

- **ev_1 to ev_10**: 10 electric vehicles modeled as ElectricVehicle assets.
  Each vehicle is a Storage with trip schedules. EVs must be assigned to a
  charger to charge or discharge.
- **battery**: A 300 kWh stationary Storage. This battery can charge and
  discharge freely without needing charger assignment, demonstrating how EVs
  and stationary storage coexist.
- **charger_1 to charger_4**: 4 chargers with different power ratings (22 kW
  to 150 kW). Each charger can serve at most one vehicle at a time.
- **solar_pv**: 100 kW solar farm, zero variable cost.
- **site_load**: Fixed building consumption separate from EV charging.
- **grid_market**: Buy/sell electricity market with time-of-use pricing.

## Problem

A commercial fleet operator wants to minimize electricity costs over a 24-hour
horizon while:
- Meeting all trip energy requirements (vehicles must have enough charge)
- Respecting charger constraints (each charger serves one vehicle at a time)
- Maximizing solar self-consumption
- Optionally selling excess energy back to the grid

Each vehicle has predefined trips that consume energy and make the vehicle
unavailable for charging during the trip. The optimizer decides when to charge
each vehicle (and which charger to use) to minimize cost while ensuring all
trips can be completed. The stationary battery can charge/discharge freely
to further optimize costs.

## Expected Results

The optimizer will:
- Charge vehicles when electricity is cheap (off-peak or high solar)
- Discharge vehicles (V2G) when electricity is expensive (if allowed)
- Prioritize solar charging when available
- Ensure all trips are completed with sufficient SoC
- Respect charger power limits and assignment constraints
- Use the stationary battery for additional arbitrage (no charger needed)

## Understanding the Output

The script prints:
- EV charging/discharging power and SoC over time
- Stationary battery power and SoC over time
- Solar generation, grid import/export
- Total electricity cost

This example demonstrates EV fleet optimization as a natural extension of the
existing Storage and market models, with trips defining availability implicitly
and chargers providing explicit assignment constraints.
"""

from datetime import timedelta

from odys import (
    AssetPortfolio,
    Charger,
    ElectricVehicle,
    EnergyMarket,
    EnergySystem,
    FixedLoad,
    Generator,
    Scenario,
    Storage,
    TradeDirection,
    Trip,
)
from odys.results.optimization_results import OptimalDisptachResults
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)


def run_ev_fleet_optimization() -> OptimalDisptachResults:
    """Run the EV fleet optimization example and return the optimization results."""
    ev_1 = ElectricVehicle(
        name="ev_1",
        capacity=50,
        max_charge_power=11,
        max_discharge_power=0,
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
        soc_start=0.8,
        soc_min=0.2,
        degradation_cost=0.01,
        trips=(
            Trip(name="ev_1_morning", start_time=8, end_time=12, energy_consumption=25, min_soc_at_departure=0.5),
            Trip(name="ev_1_afternoon", start_time=14, end_time=18, energy_consumption=20, min_soc_at_departure=0.4),
        ),
    )

    ev_2 = ElectricVehicle(
        name="ev_2",
        capacity=75,
        max_charge_power=22,
        max_discharge_power=11,
        efficiency_charging=0.95,
        efficiency_discharging=0.92,
        soc_start=0.5,
        soc_min=0.2,
        degradation_cost=0.02,
        trips=(Trip(name="ev_2_route", start_time=9, end_time=17, energy_consumption=45, min_soc_at_departure=0.6),),
    )

    ev_3 = ElectricVehicle(
        name="ev_3",
        capacity=75,
        max_charge_power=22,
        max_discharge_power=0,
        soc_start=0.6,
        soc_min=0.2,
        trips=(Trip(name="ev_3_route", start_time=7, end_time=15, energy_consumption=30, min_soc_at_departure=0.5),),
    )
    ev_4 = ElectricVehicle(
        name="ev_4",
        capacity=100,
        max_charge_power=50,
        max_discharge_power=25,
        soc_start=0.7,
        soc_min=0.2,
        trips=(Trip(name="ev_4_route", start_time=10, end_time=18, energy_consumption=50, min_soc_at_departure=0.4),),
    )
    ev_5 = ElectricVehicle(
        name="ev_5",
        capacity=100,
        max_charge_power=50,
        max_discharge_power=0,
        soc_start=0.4,
        soc_min=0.2,
        trips=(Trip(name="ev_5_route", start_time=6, end_time=14, energy_consumption=40, min_soc_at_departure=0.5),),
    )
    ev_6 = ElectricVehicle(
        name="ev_6",
        capacity=60,
        max_charge_power=11,
        max_discharge_power=0,
        soc_start=0.9,
        soc_min=0.2,
        trips=(Trip(name="ev_6_route", start_time=8, end_time=16, energy_consumption=25, min_soc_at_departure=0.6),),
    )
    ev_7 = ElectricVehicle(
        name="ev_7",
        capacity=60,
        max_charge_power=22,
        max_discharge_power=11,
        soc_start=0.5,
        soc_min=0.2,
        trips=(Trip(name="ev_7_route", start_time=9, end_time=17, energy_consumption=35, min_soc_at_departure=0.5),),
    )
    ev_8 = ElectricVehicle(
        name="ev_8",
        capacity=80,
        max_charge_power=22,
        max_discharge_power=0,
        soc_start=0.6,
        soc_min=0.2,
        trips=(Trip(name="ev_8_route", start_time=7, end_time=15, energy_consumption=40, min_soc_at_departure=0.4),),
    )
    ev_9 = ElectricVehicle(
        name="ev_9",
        capacity=80,
        max_charge_power=22,
        max_discharge_power=11,
        soc_start=0.7,
        soc_min=0.2,
        trips=(Trip(name="ev_9_route", start_time=10, end_time=18, energy_consumption=45, min_soc_at_departure=0.5),),
    )
    ev_10 = ElectricVehicle(
        name="ev_10",
        capacity=120,
        max_charge_power=150,
        max_discharge_power=50,
        soc_start=0.3,
        soc_min=0.2,
        trips=(Trip(name="ev_10_route", start_time=6, end_time=18, energy_consumption=70, min_soc_at_departure=0.3),),
    )

    battery = Storage(
        name="battery",
        capacity=300,
        max_charge_power=150,
        max_discharge_power=200,
        soc_start=0.5,
        soc_min=0.1,
    )

    charger_1 = Charger(name="charger_1", max_power=22, efficiency=0.98)
    charger_2 = Charger(name="charger_2", max_power=50, efficiency=0.97)
    charger_3 = Charger(name="charger_3", max_power=50, efficiency=0.97)
    charger_4 = Charger(name="charger_4", max_power=150, efficiency=0.95)

    solar_pv = Generator(name="solar_pv", nominal_power=100, variable_cost=0)
    site_load = FixedLoad(name="site_load")

    market = EnergyMarket(
        name="grid_market",
        max_trading_volume_per_step=500,
        trade_direction=TradeDirection.BUY_AND_SELL,
    )

    portfolio = AssetPortfolio(
        assets=[
            ev_1,
            ev_2,
            ev_3,
            ev_4,
            ev_5,
            ev_6,
            ev_7,
            ev_8,
            ev_9,
            ev_10,
            battery,
            solar_pv,
            site_load,
            charger_1,
            charger_2,
            charger_3,
            charger_4,
        ],
    )

    solar_profile = [0, 0, 0, 0, 0, 0, 5, 15, 30, 50, 70, 85, 90, 85, 70, 50, 30, 15, 5, 0, 0, 0, 0, 0]
    site_load_profile = [30, 28, 25, 25, 25, 28, 35, 45, 55, 60, 65, 65, 60, 60, 65, 65, 60, 55, 50, 45, 40, 38, 35, 32]
    market_prices = [
        0.10,
        0.10,
        0.10,
        0.10,
        0.10,
        0.10,
        0.10,
        0.15,
        0.15,
        0.15,
        0.15,
        0.15,
        0.15,
        0.15,
        0.15,
        0.15,
        0.25,
        0.25,
        0.25,
        0.25,
        0.25,
        0.15,
        0.15,
        0.10,
    ]

    scenario = Scenario(
        available_capacity_profiles={"solar_pv": solar_profile},
        fixed_load_profiles={"site_load": site_load_profile},
        market_prices={"grid_market": market_prices},
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

    logger.info("EV charging schedules")
    for ev_name in ["ev_1", "ev_2", "ev_3", "ev_4", "ev_5", "ev_6", "ev_7", "ev_8", "ev_9", "ev_10"]:
        logger.info("%s net power: %s", ev_name, result.storages.net_power.sel(storage=ev_name).values)
        logger.info("%s SoC: %s", ev_name, result.storages.soc.sel(storage=ev_name).values)

    logger.info("Stationary battery (no charger needed)")
    logger.info("battery net power: %s", result.storages.net_power.sel(storage="battery").values)
    logger.info("battery SoC: %s", result.storages.soc.sel(storage="battery").values)

    logger.info("Solar generation")
    logger.info(result.generators.power.sel(generator="solar_pv"))

    logger.info("Market transactions")
    logger.info("Buy: %s", result.markets.buy_volume.sel(market="grid_market").values)
    logger.info("Sell: %s", result.markets.sell_volume.sel(market="grid_market").values)

    logger.info("Objective value: %s", result.objective_value)
