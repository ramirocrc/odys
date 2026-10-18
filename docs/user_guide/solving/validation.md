---
icon: lucide/shield-check
---

# Validation and errors

odys checks your inputs before it builds anything, so most mistakes show up as a clear error before anything is solved.

## Validation

Creating an `EnergySystem` validates the whole configuration and raises an `OdysValidationError` on the first problem it finds. Checks that concern a single object, such as overlapping EV trips or an available capacity above a generator's nominal power, already ran when that object was built, and a non-positive `timestep` or fewer than one step is a field error (see [Errors](#errors)). The system-level checks are:

- scenario probabilities sum to 1 and scenario names are unique
- every initial and final condition references an asset of the portfolio, with at most one condition of each type per asset
- every storage and EV has an initial state, and so does every generator with ramp limits, minimum up or down times, or startup or shutdown costs
- minimum up and down times and each generator's `time_in_state` are a whole number of timesteps, and each generator's final power fits its available capacity at the last step
- every profile references an asset of the portfolio or one of the markets
- every load has a `LoadProfile`, and every market a `PriceProfile`, in every scenario
- every profile has `number_of_steps` values, and every EV trip starts and ends on a timestep and within the horizon
- in every scenario and at every timestep, the maximum supply (generators, storage and EV discharge, market volume) covers the minimum demand (fixed loads, plus flexible loads after their maximum decrease)
- without markets, the energy available over the horizon covers the minimum energy demand

For example, a profile one value short is caught when the system is created, before anything is solved:

```python
from datetime import timedelta

from odys import AssetPortfolio, EnergySystem, FixedLoad, Generator, LoadProfile, OdysValidationError, Scenario

ccgt = Generator(name="ccgt", nominal_power=100.0, variable_cost=50.0)
factory = FixedLoad(name="factory")

try:
    EnergySystem(
        portfolio=AssetPortfolio([ccgt, factory]),
        scenarios=Scenario(profiles=(LoadProfile(load=factory, values=[60, 90, 40]),)),
        timestep=timedelta(hours=1),
        number_of_steps=4,
    )
except OdysValidationError as error:
    print(error)
```

```text
Scenario 'base': the LoadProfile for 'factory' has 3 values, but the horizon has 4 steps.
```

## Errors

Odys's own errors derive from `OdysError` and are exported from `odys`, so `except odys.OdysValidationError` works:

| Exception                  | Raised when                                                                                         |
| -------------------------- | --------------------------------------------------------------------------------------------------- |
| `OdysValidationError`      | An input breaks a rule of Odys: when an asset, profile, condition or the `EnergySystem` is built     |
| `OdysSolverError`          | The requested solver is not installed, or you read results of a run that found no solution          |
| `OdysNoResultsError`       | You read a results container the system does not have, such as `result.markets` without markets     |
| `pydantic.ValidationError` | A single field is out of range or of the wrong type, such as a negative `capacity`                  |

Field types and ranges are checked by pydantic, the library Odys's inputs are built on, so they raise its `ValidationError`, which names the field.

## Next steps

Next, see how to plan against several futures, in [Stochastic optimization](../optimization/stochastic.md).
