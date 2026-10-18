---
icon: lucide/shield-check
---

# Validation and errors

odys checks your inputs as you build them, so most mistakes show up as a clear error before anything is solved: a profile one value short, a trip that overlaps another, a battery with nowhere to start. This page lists what gets rejected, when, and which error you see. A model can still pass every check and have no solution; see [When there's no solution](#when-theres-no-solution).

## When checks run

Each check runs as early as it can: as soon as the objects it needs exist.

**A field**, when you create the object. Every field has a type and a range, such as a `capacity` above 0 or an `efficiency_charging` of at most 1. A field out of range or of the wrong type raises a `pydantic.ValidationError` that names the field. pydantic is the library odys's inputs are built on, so this is the one error that isn't an odys error.

**An object**, when you create it. Rules between the fields of one object raise an `OdysValidationError`:

- a battery's `soc_min` is below its `soc_max`;
- a flexible load has a lower and an upper limit, and its `min_load` is at most its `max_load`;
- a trip ends after it starts, and a vehicle's trips don't overlap;
- a profile's values fit the asset it references: an available capacity within the generator's `nominal_power`, a flexible load's base within its limits;
- an initial or final state fits its asset: a generator's `power` is 0 or between `min_power` and `nominal_power`, a battery's `soc` within its limits, and a trip that departs at the start fits in the starting charge;
- a `GeneratorInitialState` has a `time_in_state` when the matching minimum time needs one;
- an `Objective` has a `ProfitTerm`, and at most one term of each type.

**The portfolio**, when you create the `AssetPortfolio`: asset names are unique, only assets go in it (no markets), and chargers come with electric vehicles.

**The system**, when you create the `EnergySystem`. These checks need everything together, so they run last:

- scenario probabilities add up to 1, and scenario names are unique;
- every profile references an asset of the portfolio or one of the markets, and has one value per step;
- every load has a `LoadProfile`, and every market a `PriceProfile`, in every scenario;
- every condition references an asset of the portfolio, with at most one of each type per asset;
- every storage and vehicle has an initial state, and so does every generator whose start matters (ramp limits, minimum up or down times, start-up or shut-down costs);
- every duration is a whole number of steps, and every trip lies within the horizon;
- a generator's final power fits its available capacity at the last step;
- there's something to balance: a load or a market;
- there's enough supply, roughly: at every step, the most power you could supply covers the least you must serve, and without markets, the same holds in energy over the horizon.

The system checks stop at the first problem they find.

## Examples

A field out of range is caught when you create the object, and the error names the field:

```python
import pydantic

from odys import Battery

try:
    Battery(capacity=-50.0, max_charge_power=25.0, max_discharge_power=25.0)
except pydantic.ValidationError as error:
    problem = error.errors()[0]
    print(problem["loc"], problem["msg"])
```

```text
('capacity',) Input should be greater than 0
```

A profile one value short is caught when you create the system:

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

odys's own errors derive from `OdysError`, and are exported from `odys`:

| Exception                  | Raised when                                                                                     |
| -------------------------- | ----------------------------------------------------------------------------------------------- |
| `pydantic.ValidationError` | A field is out of range or of the wrong type, such as a negative `capacity`                     |
| `OdysValidationError`      | An input breaks a rule of odys: when an object, the portfolio or the `EnergySystem` is created  |
| `OdysSolverError`          | The requested solver isn't installed, or you read results of a run that found no solution       |
| `OdysNoResultsError`       | You read a results container the system doesn't have, such as `result.markets` without markets  |

## When there's no solution

The supply check is a rough one: it looks at each step on its own, and at the most each asset could give. So a model can pass every check and still have no feasible plan. The solve then ends without a solution, `result.termination_condition` is `"infeasible"`, and reading any result raises an `OdysSolverError` (see [Solver status](results.md#solver-status)).

The usual causes are rules that hold across steps, or exact targets:

- **Exact final states.** A final state is met exactly. Combined with ramp limits, efficiencies or trips, the asset may not be able to reach it in time.
- **Ramps from a fixed start.** A generator that starts at 50 MW with a 40 MW ramp limit can't reach more than 90 MW in the first step.
- **Minimum up and down times.** A unit that has to stay on at its `min_power` may produce more than the site can absorb, and one that has to stay off may leave demand short.
- **Trips without time to charge.** A vehicle that returns late and leaves early may not regain the charge its next trip needs.
- **Caps that are too low.** A market limit or an available capacity that can't cover demand once the other assets are committed elsewhere.

To find the cause, relax one of these at a time, for example by dropping a final state or widening a limit, and solve again. The formulation lists which properties the checks guarantee, and which only a solve can tell; see [Checked before solving](../../formulation/index.md#checked-before-solving).

## Next steps

So far every plan faced a single future. Next, see how to plan against several, in [Stochastic optimization](../optimization/stochastic.md).
