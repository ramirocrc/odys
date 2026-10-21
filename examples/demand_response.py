"""A kiln buying its power at the day-ahead price.

This example plans one day of an industrial kiln that buys its power on a
supply contract indexed to the day-ahead price. The plan is made once
day-ahead has cleared on the day before, so every hourly price of the day is
known. The kiln's physics links the hours together: it ramps slowly, can't
run below its minimum stable load, and pays to restart once stopped.

## Assets

- **supply**: Buy-only supply at the day-ahead price, capped at 100 MW by the
  grid connection. Hourly prices range from 28 to 140 $/MWh.
- **kiln**: Runs between 40 and 100 MW, or not at all. Each MWh it consumes
  is worth 70 $/MWh. It ramps up by at most 20 MW per hour and down by at
  most 30 MW per hour, stays off for at least 3 hours once stopped, and each
  start costs 2,000. It is running at 40 MW at midnight.

The same day is also solved for an ideal kiln without ramps, minimum down
time or start-up cost, to show what the physics costs.

## Expected Results

- Hours 0-2: the kiln ramps from 40 to 100 MW; the ideal kiln runs at 100 MW.
- Hours 5-7: the kiln ramps down ahead of the morning peak and runs at its
  40 MW floor through it, rather than stopping and paying to restart.
- Hours 17-21: both stop for the evening peak.
- Hours 22-23: the kiln restarts straight at 100 MW.

The kiln earns 31,320, the ideal kiln 36,600: the physics costs 5,280.

## Understanding the Output

The script prints both kilns' consumption over the day and their objective
values.
"""

import logging
from datetime import timedelta
from typing import NamedTuple

from odys import (
    AllowedTradeDirection,
    AssetPortfolio,
    Commitment,
    EnergyMarket,
    EnergySystem,
    FlexibleLoad,
    FlexibleLoadInitialState,
    FlexibleLoadProfile,
    OptimalDispatchResults,
    PriceProfile,
    Scenario,
)

logger = logging.getLogger(__name__)

HOURS = 24
DAY_AHEAD_PRICES = [52, 48, 45, 44, 46, 62, 88, 92, 66, 64, 62, 35, 30, 28, 32, 40, 60, 95, 120, 140, 130, 100, 60, 50]
MIN_STABLE_LOAD = 40.0
MAX_LOAD = 100.0
VALUE_OF_CONSUMPTION = 70.0


class DemandResponseResults(NamedTuple):
    """The plans of the real kiln and of an ideal kiln without ramps, minimum down time or start-up cost."""

    kiln: OptimalDispatchResults
    ideal: OptimalDispatchResults


def _solve(kiln: FlexibleLoad, initial_conditions: tuple[FlexibleLoadInitialState, ...]) -> OptimalDispatchResults:
    supply = EnergyMarket(
        name="supply",
        max_trading_volume_per_step=MAX_LOAD,
        allowed_trade_direction=AllowedTradeDirection.BUY_ONLY,
    )

    scenario = Scenario(
        profiles=(
            FlexibleLoadProfile(load=kiln, lower_bound=HOURS * [MIN_STABLE_LOAD], upper_bound=HOURS * [MAX_LOAD]),
            PriceProfile(market=supply, values=DAY_AHEAD_PRICES),
        ),
    )

    energy_system = EnergySystem(
        portfolio=AssetPortfolio(assets=[kiln]),
        markets=supply,
        timestep=timedelta(hours=1),
        number_of_steps=HOURS,
        scenarios=scenario,
        initial_conditions=initial_conditions,
    )

    return energy_system.optimize()


def run_demand_response() -> DemandResponseResults:
    """Run the kiln example and return the plans of the real and the ideal kiln."""
    kiln = FlexibleLoad(
        name="kiln",
        value_of_consumption=VALUE_OF_CONSUMPTION,
        ramp_up=20.0,
        ramp_down=30.0,
        commitment=Commitment(min_down_time=timedelta(hours=3), startup_cost=2000.0),
    )
    ideal_kiln = FlexibleLoad(name="kiln", value_of_consumption=VALUE_OF_CONSUMPTION, commitment=Commitment())

    return DemandResponseResults(
        kiln=_solve(kiln, (FlexibleLoadInitialState(load=kiln, power=MIN_STABLE_LOAD),)),
        ideal=_solve(ideal_kiln, ()),
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("linopy").setLevel(logging.WARNING)
    results = run_demand_response()

    for label, result in results._asdict().items():
        logger.info("%s plan, objective %.0f", label, result.objective_value)
        logger.info(result.flexible_loads.consumption)
