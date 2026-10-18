"""EV fleet optimization with V2G and shared chargers.

A commercial depot operates 3 delivery EVs with 2 chargers and access to a
wholesale market with time-of-use pricing. The optimizer decides when each van
charges, when it sells power back to the grid (V2G), and which charger it
uses, while every trip departs with enough charge.

## Assets

- **ev_1**: 100 kWh battery, 22 kW charging, 11 kW V2G. Starts at 80% SoC,
  must end at 30% SoC. 3 delivery trips.
- **ev_2**: 60 kWh battery, 22 kW charging, 11 kW V2G. Starts at 50% SoC,
  must end at 60% SoC. 3 delivery trips.
- **ev_3**: 40 kWh battery, 7 kW charging, 7 kW V2G. Starts at 50% SoC,
  must end at 50% SoC. 2 delivery trips.
- **charger_dc**: 50 kW DC fast charger. Serves one EV at a time.
- **charger_ac**: 22 kW AC charger. Serves one EV at a time.
- **grid_market**: Buy-and-sell market with time-of-use pricing (5-100 $/MWh)
  and 100 kW max trading volume.

## Expected Results

The vans charge at 5 and 10 $/MWh and sell back at the morning and evening
peaks. At every evening peak step, both chargers are discharging a van; when
all three vans are parked, one of them waits. The day's profit is 9.99.

## Understanding the Output

The script prints:
- EV charging/discharging power and SoC over time
- Charger assignment over time (shows which EV is connected to which charger)
- Market buy and sell volumes
- Objective value (profit, positive = revenue)
"""

import logging
from datetime import timedelta

from odys import (
    AssetPortfolio,
    Battery,
    Charger,
    ElectricVehicle,
    ElectricVehicleFinalState,
    ElectricVehicleInitialState,
    EnergyMarket,
    EnergySystem,
    OptimalDispatchResults,
    PriceProfile,
    Scenario,
    Trip,
)

logger = logging.getLogger(__name__)

ev_1 = ElectricVehicle(
    name="ev_1",
    battery=Battery(
        capacity=0.100,  # 100 kWh
        max_charge_power=0.022,  # 22 kW
        max_discharge_power=0.011,  # 11 kW V2G
    ),
    trips=(
        Trip(
            name="morning_delivery",
            start_time=timedelta(hours=7),
            end_time=timedelta(hours=9),
            energy_consumption=0.015,  # 15 kWh
            min_soc_at_departure=0.6,
        ),
        Trip(
            name="midday_delivery",
            start_time=timedelta(hours=11),
            end_time=timedelta(hours=12),
            energy_consumption=0.010,  # 10 kWh
            min_soc_at_departure=0.4,
        ),
        Trip(
            name="afternoon_delivery",
            start_time=timedelta(hours=14),
            end_time=timedelta(hours=16),
            energy_consumption=0.012,  # 12 kWh
            min_soc_at_departure=0.3,
        ),
    ),
)

ev_2 = ElectricVehicle(
    name="ev_2",
    battery=Battery(
        capacity=0.060,  # 60 kWh
        max_charge_power=0.022,  # 22 kW
        max_discharge_power=0.011,  # 11 kW V2G
    ),
    trips=(
        Trip(
            name="morning_route",
            start_time=timedelta(hours=8),
            end_time=timedelta(hours=10),
            energy_consumption=0.008,  # 8 kWh
            min_soc_at_departure=0.5,
        ),
        Trip(
            name="midday_route",
            start_time=timedelta(hours=12),
            end_time=timedelta(hours=13),
            energy_consumption=0.006,  # 6 kWh
            min_soc_at_departure=0.35,
        ),
        Trip(
            name="evening_route",
            start_time=timedelta(hours=17),
            end_time=timedelta(hours=19),
            energy_consumption=0.007,  # 7 kWh
            min_soc_at_departure=0.25,
        ),
    ),
)

ev_3 = ElectricVehicle(
    name="ev_3",
    battery=Battery(
        capacity=0.040,  # 40 kWh
        max_charge_power=0.007,  # 7 kW
        max_discharge_power=0.007,  # 7 kW V2G
    ),
    trips=(
        Trip(
            name="delivery_1",
            start_time=timedelta(hours=9),
            end_time=timedelta(hours=11),
            energy_consumption=0.005,  # 5 kWh
            min_soc_at_departure=0.5,
        ),
        Trip(
            name="delivery_2",
            start_time=timedelta(hours=14),
            end_time=timedelta(hours=15),
            energy_consumption=0.003,  # 3 kWh
            min_soc_at_departure=0.3,
        ),
    ),
)

EVS: tuple[ElectricVehicle, ...] = (ev_1, ev_2, ev_3)

EV_INITIAL_STATES: tuple[ElectricVehicleInitialState, ...] = (
    ElectricVehicleInitialState(vehicle=ev_1, soc=0.8),
    ElectricVehicleInitialState(vehicle=ev_2, soc=0.5),
    ElectricVehicleInitialState(vehicle=ev_3, soc=0.5),
)

EV_FINAL_STATES: tuple[ElectricVehicleFinalState, ...] = (
    ElectricVehicleFinalState(vehicle=ev_1, soc=0.3),
    ElectricVehicleFinalState(vehicle=ev_2, soc=0.6),
    ElectricVehicleFinalState(vehicle=ev_3, soc=0.5),
)

CHARGERS: tuple[Charger, ...] = (
    Charger(name="charger_dc", max_power=0.050),  # 50 kW
    Charger(name="charger_ac", max_power=0.022),  # 22 kW
)

MARKET_PRICES: list[float] = [
    *6 * [5.0],  # overnight: cheap
    *2 * [20.0],  # morning ramp
    *2 * [80.0],  # morning peak
    *5 * [10.0],  # midday: cheap
    *2 * [25.0],  # evening ramp
    *4 * [100.0],  # evening peak
    *3 * [5.0],  # late evening: cheap
]


def run_ev_fleet_optimization() -> OptimalDispatchResults:
    """Run the EV fleet optimization example and return the optimization results."""
    market = EnergyMarket(
        name="grid_market",
        max_trading_volume_per_step=0.100,  # 100 kW
    )

    portfolio = AssetPortfolio([*EVS, *CHARGERS])

    scenario = Scenario(profiles=(PriceProfile(market=market, values=MARKET_PRICES),))

    energy_system = EnergySystem(
        portfolio=portfolio,
        markets=market,
        timestep=timedelta(hours=1),
        number_of_steps=24,
        scenarios=scenario,
        initial_conditions=EV_INITIAL_STATES,
        final_conditions=EV_FINAL_STATES,
    )

    return energy_system.optimize()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("linopy").setLevel(logging.WARNING)
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
