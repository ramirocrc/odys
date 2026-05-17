"""Basic dispatch optimization.

This example shows the simplest possible Odys workflow: use a cheap renewable
generator first, then fill the remaining demand with a more expensive thermal
generator.

## Assets

- **solar_pv**: 150 MW solar farm, zero variable cost (free energy), but
  output depends on weather and time of day.
- **ccgt**: 100 MW gas turbine, variable cost of 50 $/MWh, fully available
  24/7.

## Problem

We simulate 9 half-hour periods (4.5 hours) with a constant 70 MW load.
The solar profile ramps up from 0 to 100 MW and then back down, which gives
the optimizer a mix of easy and constrained timesteps to work through.

## Expected Results

Since solar has zero marginal cost, the optimizer uses it first. The gas plant
only covers whatever demand solar cannot meet.

For example:
- When solar = 70 MW available, ccgt = 0  (demand fully met by solar)
- When solar = 30 MW available, ccgt = 40  (30 from solar, 40 from gas)
- When solar = 0 MW, ccgt = 70  (all demand from gas)

## Understanding the Output

The script prints:
- Individual generator dispatch as DataFrames (power at each timestep)
- Combined power output across all generators

The main lesson is that nominal capacity is only part of the picture. The
available capacity profile is what actually determines how much solar can be
used at each step.
"""

from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, Generator, Load, LoadType, Scenario
from odys.utils.logging import get_logger, setup_rich_logging

setup_rich_logging()
logger = get_logger(__name__)

if __name__ == "__main__":
    ccgt = Generator(
        name="ccgt",
        nominal_power=100,
        variable_cost=50,
    )
    solar_pv = Generator(
        name="solar_pv",
        nominal_power=150,
        variable_cost=0,
    )
    load = Load(name="load", type=LoadType.Fixed)
    portfolio = AssetPortfolio([ccgt, solar_pv, load])

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

    result = energy_system.optimize()
    logger.info("Generators optimal dispatch")
    for gen_dispatch in result.generators:
        logger.info(gen_dispatch.to_dataframe())

    logger.info("All generators power")
    logger.info(result.generators.power)
