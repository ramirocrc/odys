# Optimization

This page explains what happens when you call `energy_system.optimize()` -- the objective function, the constraints, and how to read the results.

## Objective function

Odys minimizes the total system cost (or equivalently, maximizes profit). The objective has two components:

**Operating costs** (minimized):

- Generator variable costs: `power_output * variable_cost` for each generator at each timestep
- Startup costs: `startup_cost` each time a generator turns on

**Market revenue** (maximized):

- Revenue from selling energy: `sell_volume * market_price`
- Cost of buying energy: `buy_volume * market_price`

The optimizer finds the dispatch schedule that produces the best net profit across all timesteps (and all scenarios, if you're using stochastic optimization).

## Constraints

The optimizer respects these constraints:

### Power balance

At every timestep, supply must equal demand:

```
generator_output + battery_discharge + market_buys
= load + battery_charge + market_sells
```

This is the fundamental constraint -- the system has to balance.

### Generator constraints

- **Max power**: Output can't exceed `nominal_power * status`
- **Min power**: When on, output must be at least `min_power`
- **Ramp up/down**: Change in output between consecutive steps is bounded
- **Min up time**: Once on, the generator stays on for at least `min_up_time` steps
- **Startup/shutdown logic**: Binary variables track when generators turn on and off
- **Available capacity**: If `available_capacity_profiles` is provided, output is capped per timestep

### Battery constraints

- **SOC tracking**: State of charge is updated based on charge/discharge and efficiency
- **SOC bounds**: SOC stays within `[soc_min, soc_max]`
- **Initial/final SOC**: Honored as set on the `Battery` object
- **Power limits**: Charge and discharge can't exceed `max_power`

### Market constraints

- **Volume limits**: Buy/sell volume per timestep can't exceed `max_trading_volume_per_step`
- **Trade direction**: If a market is buy-only or sell-only, the other direction is zero
- **Non-anticipativity**: For `stage_fixed` markets, trading volumes are the same across all scenarios

## Reading results

The `optimize()` call returns an `OptimizationResults` object:

```python
result = energy_system.optimize()
```

### Solver status

```python
result.solver_status         # "ok" if the solver found a solution
result.termination_condition # "optimal" if it's the best possible solution
```

### Asset-specific results

Each asset type has its own results container:

```python
# Generators
result.generators.power     # MW dispatched per timestep
result.generators.status    # on/off (1/0)
result.generators.startup   # startup events
result.generators.shutdown  # shutdown events

# Batteries
result.batteries.net_power        # positive = discharging, negative = charging
result.batteries.state_of_charge  # SOC at each timestep

# Markets
result.markets.sell_volume  # MW sold per market per timestep
result.markets.buy_volume   # MW bought per market per timestep
```

All of these are `pandas.DataFrame` objects, so you can use the full pandas API to slice, filter, and plot.

### Combined DataFrame

For a single view of everything:

```python
df = result.to_dataframe
```

This gives you a multi-indexed DataFrame with all variables, units, and timesteps. For deterministic scenarios, the scenario index level is dropped automatically.

!!! tip

    If you're working in a notebook, `result.to_dataframe` is usually the quickest way to see what the optimizer did. You can export it with `.to_csv()` or plot it directly.
