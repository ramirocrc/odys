"""Landing page hero snippet: one price forecast, one schedule."""

import runpy
from datetime import timedelta
from pathlib import Path

from odys import (
    AssetPortfolio,
    Battery,
    EnergyMarket,
    EnergySystem,
    PriceProfile,
    Scenario,
    StationaryStorage,
)

forecast = runpy.run_path(str(Path(__file__).with_name("prices.py")))["forecast"]

# --8<-- [start:shown]
battery = StationaryStorage(
    name="bess",
    battery=Battery(
        capacity=100,
        max_charge_power=30,
        max_discharge_power=30,
        efficiency_charging=0.95,
        efficiency_discharging=0.95,
        soc_start=0.5,
        soc_end=0.5,
    ),
)
market = EnergyMarket(
    name="day_ahead",
    max_trading_volume_per_step=30,
    stage_fixed=True,
)

system = EnergySystem(
    portfolio=AssetPortfolio([battery]),
    markets=[market],
    scenarios=Scenario(
        profiles=(
            PriceProfile(
                market=market,
                values=forecast,
            ),
        ),
    ),
    timestep=timedelta(hours=1),
    number_of_steps=24,
)
result = system.optimize()
# --8<-- [end:shown]
