"""Landing page hero snippet: one price forecast, one schedule."""

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

# One point forecast of hourly day-ahead prices (€/MWh)
forecast = [42, 36, 31, 37, 33, 37, 58, 71, 84, 66, 57, 42, 34, 33, 44, 58, 89, 114, 127, 120, 95, 79, 48, 42]

# A single scenario with the forecast prices
scenarios = Scenario(
    profiles=(PriceProfile(market=market, values=forecast),),
)

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
