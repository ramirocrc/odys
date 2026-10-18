"""Landing page hero snippet: twelve price scenarios, one schedule."""

from datetime import timedelta

from odys import (
    AssetPortfolio,
    Battery,
    BatteryStorage,
    EnergyMarket,
    EnergySystem,
    PriceProfile,
    Scenario,
    StorageFinalState,
    StorageInitialState,
)

# --8<-- [start:shown]
battery = BatteryStorage(
    name="bess",
    battery=Battery(
        capacity=100,
        max_charge_power=30,
        max_discharge_power=30,
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
    ),
)
market = EnergyMarket(
    name="day_ahead",
    max_trading_volume_per_step=30,
    stage_fixed=True,
)
initial = StorageInitialState(
    storage=battery,
    soc=0.5,
)
final = StorageFinalState(
    storage=battery,
    soc=0.5,
)

# 12 scenarios of hourly day-ahead prices (€/MWh)
price_scenarios = [
    [45, 42, 46, 37, 38, 52, 65, 80, 88, 77, 37, 27, 27, 25, 28, 39, 80, 106, 110, 100, 83, 68, 60, 51],
    [42, 36, 31, 37, 33, 37, 58, 71, 84, 66, 57, 42, 34, 33, 44, 58, 89, 114, 127, 120, 95, 79, 48, 42],
    [43, 37, 35, 32, 40, 43, 56, 79, 80, 67, 67, 53, 35, 40, 42, 57, 75, 101, 116, 101, 87, 66, 53, 47],
    [45, 40, 41, 32, 34, 43, 57, 81, 86, 72, 73, 56, 46, 45, 46, 68, 94, 125, 142, 127, 105, 80, 54, 46],
    [43, 36, 40, 36, 33, 42, 54, 77, 79, 66, 68, 54, 44, 38, 49, 65, 53, 72, 81, 76, 56, 45, 54, 52],
    [44, 39, 31, 32, 29, 42, 57, 76, 81, 65, 67, 45, 34, 34, 42, 58, 82, 107, 115, 105, 84, 71, 49, 48],
    [51, 45, 48, 38, 41, 49, 61, 80, 91, 79, 54, 44, 36, 30, 39, 48, 86, 106, 114, 108, 89, 75, 61, 57],
    [42, 40, 36, 35, 33, 42, 51, 76, 78, 63, 45, 32, 24, 26, 25, 42, 73, 98, 108, 92, 79, 67, 48, 41],
    [51, 56, 49, 43, 47, 51, 72, 88, 92, 79, 46, 36, 29, 27, 34, 44, 80, 102, 114, 104, 84, 70, 63, 59],
    [36, 36, 37, 35, 31, 42, 58, 72, 81, 65, 53, 42, 29, 31, 39, 56, 75, 96, 115, 101, 84, 66, 52, 43],
    [50, 49, 45, 42, 48, 47, 65, 80, 93, 77, 42, 31, 29, 26, 28, 36, 70, 91, 100, 93, 78, 66, 64, 55],
    [42, 45, 37, 33, 38, 46, 60, 77, 86, 69, 49, 41, 33, 34, 35, 52, 67, 88, 103, 88, 71, 58, 55, 49],
]

# One scenario per price series, all equally likely
scenarios = [
    Scenario(
        name=f"scenario_{i}",
        probability=1 / len(price_scenarios),
        profiles=(PriceProfile(market=market, values=prices),),
    )
    for i, prices in enumerate(price_scenarios)
]

system = EnergySystem(
    portfolio=AssetPortfolio([battery]),
    markets=[market],
    scenarios=scenarios,
    timestep=timedelta(hours=1),
    number_of_steps=24,
    initial_conditions=[initial],
    final_conditions=[final],
)
result = system.optimize()
# --8<-- [end:shown]
