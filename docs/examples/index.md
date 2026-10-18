---
icon: lucide/flask-conical
---

# Examples

Each example solves one planning problem end to end: it states the problem, walks through the script that models it, and reads the results. Every number on a page comes from running its script. They build on each other in order, and link to the [User Guide](../user_guide/index.md) for each feature they use.

| Example | The question | Uses |
| ------- | ------------ | ---- |
| [Basic Dispatch](basic_dispatch.md) | How much of a constant load can solar cover, and how much gas is left? | Generators, a fixed load, available capacity |
| [Battery Dispatch](battery_dispatch.md) | How much midday solar is worth storing for the evening, with losses? | Stationary storage, initial and final state |
| [Flexible Load Market](flexible_load_market.md) | How much should a process consume at each hour, given what power is worth to it? | A flexible load, a buy-only market with a volume limit |
| [Market Arbitrage](market_arbitrage.md) | When should a CCGT produce, buy instead, or run flat out to sell? | A buy-and-sell market |
| [CVaR Market Risk](cvar_market_risk.md) | How much to commit day-ahead, when a bad outcome weighs more than a good one? | Scenarios, a stage-fixed market, a CVaR term |
| [EV Fleet Optimization](ev_fleet_optimization.md) | When should three vans charge and sell back, when they share two chargers? | Electric vehicles, trips, chargers, V2G |

## Running the examples

The scripts are in the [`examples/`](https://github.com/ramirocrc/odys/tree/main/examples) directory of the repository. Each one wraps its model in a `run_...()` function that returns the results, and prints them when run on its own. From a clone of the repository, with odys installed:

```bash
python examples/basic_dispatch.py
python examples/battery_dispatch.py
python examples/flexible_load_market.py
python examples/market_arbitrage.py
python examples/cvar_market_risk.py
python examples/ev_fleet_optimization.py
```
