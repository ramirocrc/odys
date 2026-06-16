"""Battery dispatch with solar and storage.

This example shows how storage changes the dispatch problem. Instead of using
solar as soon as it is available and then falling back to gas, the optimizer
can save extra solar for later.

## Assets

- **solar_pv**: 150 MW solar farm, zero variable cost, output depends on
  weather and time of day.
- **ccgt**: 100 MW gas turbine, variable cost of 50 $/MWh.
- **battery**: 100 MWh capacity, 200 MW max charge/discharge rate.
  Starts and ends empty (soc_start=0, soc_end=0).

## Problem

The setup is still 9 half-hour periods with a constant 70 MW load. The
optimizer can now:
1. Use solar to meet load
2. Store excess solar in the battery when production is above demand
3. Discharge the battery when solar is below demand
4. Use ccgt as backup

## Expected Results

Because solar is free, the optimizer tries to use every available megawatt.
The battery acts like a buffer: it absorbs surplus energy and returns it later
when solar is scarce.

For example:
- When solar = 100 MW: battery charges at 30 MW, ccgt = 0  # free charging
- When solar = 0 MW, battery fully charged: ccgt = 0  # battery powers load
- When solar = 0 MW, battery empty: ccgt = 100  # must generate from gas (more than load to charge)

## Understanding the Output

The script prints:
- Generator power output at each timestep
- Battery power flow over time

The important point is not the sign convention itself, but the pattern: charge
when solar is plentiful, discharge when demand would otherwise be served by
gas.

"""

from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, Generator, Load, LoadType, Scenario, Storage
from odys.results.optimization_results import OptimalDisptachResults
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)


def run_battery_dispatch() -> OptimalDisptachResults:
    """Run the battery dispatch example and return the optimization results."""
    generator_1 = Generator(
        name="ccgt",
        nominal_power=100,
        variable_cost=50,
    )
    generator_2 = Generator(
        name="solar_pv",
        nominal_power=150,
        variable_cost=0,
    )
    load = Load(name="load", type=LoadType.Fixed)

    battery = Storage(
        name="battery",
        capacity=100,
        max_power=200,
        soc_start=0,
        soc_end=0,
    )
    portfolio = AssetPortfolio(assets=[generator_1, generator_2, load, battery])

    scenario = Scenario(
        available_capacity_profiles={
            "ccgt": 9 * [100],
            "solar_pv": [0, 30, 60, 80, 100, 80, 60, 30, 0],
        },
        load_profiles={
            "load": 9 * [70],
        },
    )
    energy_system = EnergySystem(
        portfolio=portfolio,
        timestep=timedelta(minutes=30),
        number_of_steps=9,
        scenarios=scenario,
    )

    return energy_system.optimize()


if __name__ == "__main__":
    result = run_battery_dispatch()
    logger.info("generators power")
    logger.info(result.generators.power)

    logger.info("battery net power")
    logger.info(result.storages.net_power)
