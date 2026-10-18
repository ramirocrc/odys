---
icon: lucide/flask-conical
---

# Examples

Each example solves one planning problem end to end: it states the problem, walks through the script that models it, and reads the results. Every number on a page comes from running its script. They build on each other in order, and link to the [User Guide](../user_guide/model/first_model.md) for each feature they use.

| Example | The question | Uses |
| ------- | ------------ | ---- |
| [Merit-Order Dispatch](merit_order_dispatch.md) | How much of a constant load can solar cover, and how much gas is left? | Generators, a fixed load, available capacity |
| [Storing Solar for the Evening](solar_storage.md) | How much midday solar is worth storing for the evening, with losses? | Battery storage, initial and final state |
| [Industrial Demand Response](demand_response.md) | How much should a process consume at each hour, given what power is worth to it? | A flexible load, a buy-only market with a volume limit |
| [Make or Buy](make_or_buy.md) | When should a CCGT produce, buy instead, or run flat out to sell? | A buy-and-sell market |
| [Day-Ahead or Intraday](day_ahead_or_intraday.md) | How much to commit day-ahead, when a bad outcome weighs more than a good one? | Scenarios, a stage-fixed market, a CVaR term |
| [Depot Charging with V2G](depot_charging.md) | When should three vans charge and sell back, when they share two chargers? | Electric vehicles, trips, chargers, V2G |

## Running the examples

The scripts are in the [`examples/`](https://github.com/ramirocrc/odys/tree/main/examples) directory of the repository. Each one wraps its model in a `run_...()` function that returns the results, and prints them when run on its own. From a clone of the repository, with odys installed:

```bash
python examples/merit_order_dispatch.py
python examples/solar_storage.py
python examples/demand_response.py
python examples/make_or_buy.py
python examples/day_ahead_or_intraday.py
python examples/depot_charging.py
```
